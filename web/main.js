async function createPublicationBrowserAsync($browserElement, indexJsonUrl) {
    const indexJson = await fetch(indexJsonUrl).then((response) => response.json());
    const browser = new PublicationBrowser($browserElement, indexJson);
    return browser;
}

function PublicationBrowser($browserElement, indexJson) {
    this.$browserElement = $browserElement;
    this.indexJson = indexJson;
    this.$browserElement.innerHTML = "";
    this.$browserElement.classList.add('publication-browser');
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
