function makePublicationBrowser($browserElement, publicationIds) {
    // const indexJson = await fetch(indexJsonUrl).then((response) => response.json());
    const browser = new PublicationBrowser($browserElement, publicationIds);
    return browser;
}
function PublicationBrowser($browserElement, publicationIds) {
    this.$browserElement = $browserElement;
    this.publicationIds = publicationIds;
    this.$browserElement.innerHTML = "";
    this.$browserElement.classList.add('publication-browser');
    this.$pub = document.createElement('div');
    this.$pub.classList.add('publication');
    this.$browserElement.appendChild(this.$pub);
    this.pdirCache = {};
    this.showPublicationAsync(publicationIds[0]);
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
PublicationBrowser.prototype.showPublicationAsync = async function(pubId) {
    if (typeof pubId !== "string") {
        this.$pub.innerText = "No publication selected";
        return;
    }
    const pdirUrl = "p/" + pubId.slice(0, 4) + ".json";
    this.$pub.innerText = `Loading ${pubId}...`;
    const pub = await this.getPublicationAsync(pubId);
    this.$pub.innerHTML = pub.html;
}
PublicationBrowser.prototype.setPublicationIdsAsync = async function(newPubIds) {
    this.publicationIds = newPubIds;
    await this.showPublicationAsync(newPubIds[0]);
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
PublicationSearch.prototype.searchAsync = async function(query) {
    const parts = query.split(" ");
    const foundPubIds = [];
    for (let part of parts) {
        const pubIds = await this.searchPartAsync(part);
        for (let pubId of pubIds) {
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
    // console.log(wordIndex);
    const pubIds = index[word];
    console.log("word", word, pubIds);
    return pubIds || [];
}
PublicationSearch.prototype.searchIdAsync = async function(pubId) {
    if (pubId.length < 7) {
        return [];
    }
    const indexUrl = "p/" + pubId.toLowerCase().slice(0, 4) + ".json";
    const index = await (await fetch(indexUrl)).json();
    if (pubId in index) {
        return [pubId];
    }
    else {
        return [];
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
