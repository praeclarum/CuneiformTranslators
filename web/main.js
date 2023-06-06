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
    const pdirUrl = "p/" + pubId.slice(0, 4) + ".json";
    this.$pub.innerText = `Loading ${pubId}...`;
    const pub = await this.getPublicationAsync(pubId);
    this.$pub.innerHTML = pub.html;
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
