function makePublicationBrowser($browserElement, publicationIds) {
    // const indexJson = await fetch(indexJsonUrl).then((response) => response.json());
    const browser = new PublicationBrowser($browserElement, publicationIds);
    return browser;
}
function PublicationBrowser($browserElement, publicationIds) {
    this.pdirCache = {};
    this.publicationIds = publicationIds;
    this.selectedIndex = 0;
    this.$browserElement = $browserElement;
    this.$browserElement.innerHTML = "";
    this.$browserElement.classList.add('publication-browser');
    this.$selectPrevious = document.createElement('button');
    this.$selectPrevious.classList.add('select-button');
    this.$selectPrevious.innerText = "<";
    this.$selectPrevious.addEventListener('click', () => this.selectPrevious());
    this.$selectNext = document.createElement('button');
    this.$selectNext.classList.add('select-button');
    this.$selectNext.innerText = ">";
    this.$selectNext.addEventListener('click', () => this.selectNext());
    this.$selectionText = document.createElement('span');
    this.$selectionText.classList.add('selection-text');
    const $selectionContainer = document.createElement('div');
    $selectionContainer.classList.add('selection-container');
    this.$browserElement.appendChild($selectionContainer);
    this.$pubsContainer = document.createElement('div');
    this.$pubsContainer.classList.add('pubs-container');
    $selectionContainer.appendChild(this.$selectPrevious);
    $selectionContainer.appendChild(this.$selectionText);
    $selectionContainer.appendChild(this.$selectNext);
    this.$browserElement.appendChild(this.$pubsContainer);
    this.$pub = document.createElement('div');
    this.$pub.classList.add('pub');
    this.$pubsContainer.appendChild(this.$pub);
    this.showPublicationAsync(this.selectedIndex);
}
PublicationBrowser.prototype.getPublicationAsync = async function(pubId) {
    const pdirUrl = "/p/" + pubId.slice(0, 4).toLowerCase() + ".json";
    if (this.pdirCache[pdirUrl] == null) {
        this.pdirCache[pdirUrl] = await fetch(pdirUrl).then((response) => response.json());
    }
    const pdir = this.pdirCache[pdirUrl];
    const pub = pdir[pubId];
    return pub;
}
PublicationBrowser.prototype.showPublicationAsync = async function(pubIndex) {
    if (pubIndex < 0 || pubIndex >= this.publicationIds.length) {
        this.$pub.innerText = `Bad pub index: ${pubIndex}`;
        return;
    }
    this.selectedIndex = pubIndex;
    this.$selectionText.innerText = `${this.selectedIndex + 1} / ${this.publicationIds.length}`;
    this.$selectPrevious.disabled = this.selectedIndex <= 0;
    this.$selectNext.disabled = this.selectedIndex >= this.publicationIds.length - 1;
    const pubId = this.publicationIds[this.selectedIndex];
    const pdirUrl = "p/" + pubId.slice(0, 4) + ".json";
    // this.$pub.innerText = `Loading ${pubId}...`;
    const pub = await this.getPublicationAsync(pubId);
    this.$pub.innerHTML = pub.html;
}
PublicationBrowser.prototype.selectPrevious = async function() {
    if (this.selectedIndex > 0) {
        await this.showPublicationAsync(this.selectedIndex - 1);
    }
}
PublicationBrowser.prototype.selectNext = async function() {
    if (this.selectedIndex < this.publicationIds.length - 1) {
        await this.showPublicationAsync(this.selectedIndex + 1);
    }
}
PublicationBrowser.prototype.setPublicationIdsAsync = async function(newPubIds) {
    this.publicationIds = newPubIds;
    this.selectedIndex = 0;
    await this.showPublicationAsync(this.selectedIndex);
}

function makePublicationSearch($searchElement) {
    const browser = new PublicationSearch($searchElement);
    return browser;
}
function PublicationSearch($searchElement, initialQuery) {
    this.$searchElement = $searchElement;
    this.$searchElement.innerHTML = "";
    this.$searchElement.classList.add('publication-search');
    this.$searchElement.innerHTML = `
        <div class="search-input-container">
            <input class="search-input" type="text" placeholder="Search" value="${initialQuery || ""}"/>
        </div>
        <div class="browser">
        </div>
        <div class="search-results-container">
            <div class="search-results"></div>
        </div>
    `;
    this.$browser = this.$searchElement.querySelector('.browser');
    this.browser = new PublicationBrowser(this.$browser, []);
    this.$searchInput = this.$searchElement.querySelector('.search-input');
    this.$searchResults = this.$searchElement.querySelector('.search-results');
    this.$searchInput.addEventListener('input', () => this.onSearchInput());
}
PublicationSearch.prototype.onSearchInput = async function() {
    const query = this.$searchInput.value;
    await this.searchAsync(query);    
}
PublicationSearch.prototype.searchAsync = async function(query, setText) {
    if (setText) {
        this.$searchInput.value = query;
    }
    const parts = query.split(" ");
    const foundPubIds = [];
    for (let part of parts) {
        const pubIdAndCounts = await this.searchPartAsync(part);
        for (let [pubId, count] of pubIdAndCounts) {
            if (!foundPubIds.includes(pubId)) {
                foundPubIds.push(pubId);
            }
        }
    }
    this.$searchResults.innerHTML = `Found ${foundPubIds.length} publications`;
    for (let result of foundPubIds) {
        const $result = document.createElement('div');
        $result.classList.add('search-result');
        $result.innerText = JSON.stringify(result);
        this.$searchResults.appendChild($result);
    }
    await this.browser.setPublicationIdsAsync(foundPubIds);
}
PublicationSearch.prototype.searchPartAsync = async function(part) {
    if (part.length < 2) {
        return [];
    }
    if (/^[PQX]\d+$/.test(part)) {
        return await this.searchIdAsync(part);
    }
    else {
        return await this.searchWordAsync(part);
    }
}
PublicationSearch.prototype.searchWordAsync = async function(word) {
    word = word.toLowerCase();
    const indexUrl = "en_index/" + word.slice(0, 2) + ".json";
    const index = await (await fetch(indexUrl)).json();
    if (word in index) {
        const pubIdAndCounts = index[word];
        console.log("word", word, pubIdAndCounts);
        return pubIdAndCounts;
    }
    else {
        const words = Object.keys(index);
        const prefixed = words.filter((w) => w.startsWith(word));
        const pubIdAndCounts = [];
        for (let w of prefixed) {
            pubIdAndCounts.push(...index[w]);
        }
        console.log("word", word, pubIdAndCounts);
        return pubIdAndCounts;
    }
}
PublicationSearch.prototype.searchIdAsync = async function(pubId) {
    if (pubId.length < 4) {
        return [];
    }
    const indexUrl = "p/" + pubId.toLowerCase().slice(0, 4) + ".json";
    const index = await (await fetch(indexUrl)).json();
    if (pubId in index) {
        return [[pubId, 1000]];
    }
    else {
        const pubIds = Object.keys(index);
        const prefixed = pubIds.filter((id) => id.startsWith(pubId));
        return prefixed.map((id) => [id, 1000 - id.length]);
    }
}


const lines = document.querySelectorAll('.line');
for (let $line of lines) {
    let matchedElements = [];
    $line.addEventListener("mouseenter", function( event ) {
        let p = event.target.parentElement;
        while (p != null && !p.classList.contains('translations-container')) {
            p = p.parentElement;
        }        
        if (p != null) {
            let linen = "line-";
            for (let c of event.target.classList) {
                if (c.startsWith('line-')) {
                    linen = c + "";
                }
            }
            function highlight(e) {
                if (e === event.target)
                    return;
                if (e.classList.contains(linen)) {
                    e.classList.add('line-match');
                    matchedElements.push(e);
                }
                else {
                    for (let c of e.children) {
                        highlight(c);
                    }
                }
            }
            highlight(p);
        }
        
    });
    $line.addEventListener("mouseleave", function( event ) {
        for (let e of matchedElements) {
            e.classList.remove('line-match');
        }
    });
}
