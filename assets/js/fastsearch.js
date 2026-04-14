import * as params from '@params';

let fuse;
let resList = document.getElementById('searchResults');
let sInput = document.getElementById('searchInput');
let first;
let last;
let currentElem = null;
let resultsAvailable = false;

function renderMessage(message) {
    resultsAvailable = false;
    resList.innerHTML = `<li class="post-entry search-message">${message}</li>`;
}

function summaryText(item) {
    return (item.summary || item.content || '').trim().slice(0, 120);
}

window.onload = function () {
    let xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function () {
        if (xhr.readyState !== 4) {
            return;
        }
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText);
            if (data) {
                let options = {
                    distance: 100,
                    threshold: 0.4,
                    ignoreLocation: true,
                    keys: ['title', 'permalink', 'summary', 'content'],
                };
                if (params.fuseOpts) {
                    options = {
                        isCaseSensitive: params.fuseOpts.iscasesensitive ?? false,
                        includeScore: params.fuseOpts.includescore ?? false,
                        includeMatches: params.fuseOpts.includematches ?? false,
                        minMatchCharLength: params.fuseOpts.minmatchcharlength ?? 1,
                        shouldSort: params.fuseOpts.shouldsort ?? true,
                        findAllMatches: params.fuseOpts.findallmatches ?? false,
                        keys: params.fuseOpts.keys ?? ['title', 'permalink', 'summary', 'content'],
                        location: params.fuseOpts.location ?? 0,
                        threshold: params.fuseOpts.threshold ?? 0.4,
                        distance: params.fuseOpts.distance ?? 100,
                        ignoreLocation: params.fuseOpts.ignorelocation ?? true,
                    };
                }
                fuse = new Fuse(data, options);
            }
            renderMessage('输入关键词后开始搜索。');
        } else {
            renderMessage('搜索索引暂时不可用，请稍后刷新页面再试。');
            console.log(xhr.responseText);
        }
    };
    xhr.open('GET', '../index.json');
    xhr.send();
};

function activeToggle(activeElement) {
    document.querySelectorAll('.focus').forEach(function (element) {
        element.classList.remove('focus');
    });
    if (activeElement) {
        activeElement.focus();
        document.activeElement = currentElem = activeElement;
        activeElement.parentElement.classList.add('focus');
    } else {
        document.activeElement.parentElement.classList.add('focus');
    }
}

function reset() {
    resultsAvailable = false;
    sInput.value = '';
    sInput.focus();
    renderMessage('输入关键词后开始搜索。');
}

sInput.onkeyup = function () {
    if (!fuse) {
        return;
    }

    let query = this.value.trim();
    if (!query) {
        renderMessage('输入关键词后开始搜索。');
        return;
    }

    let results;
    if (params.fuseOpts) {
        results = fuse.search(query, { limit: params.fuseOpts.limit });
    } else {
        results = fuse.search(query);
    }

    if (!results.length) {
        renderMessage(`没有找到“${query}”相关内容，试试标题里的词、摘要里的短句，或换一个更短的关键词。`);
        return;
    }

    let resultSet = '';
    for (let item in results) {
        let entry = results[item].item;
        let summary = summaryText(entry);
        resultSet += `<li class="post-entry">
            <header class="entry-header">${entry.title}&nbsp;»</header>
            ${summary ? `<div class="entry-content">${summary}</div>` : ''}
            <a href="${entry.permalink}" aria-label="${entry.title}"></a>
        </li>`;
    }

    resList.innerHTML = resultSet;
    resultsAvailable = true;
    first = resList.firstChild;
    last = resList.lastChild;
};

sInput.addEventListener('search', function () {
    if (!this.value) {
        reset();
    }
});

document.onkeydown = function (e) {
    let key = e.key;
    let activeElement = document.activeElement;
    let inbox = document.getElementById('searchbox').contains(activeElement);

    if (activeElement === sInput) {
        let elements = document.getElementsByClassName('focus');
        while (elements.length > 0) {
            elements[0].classList.remove('focus');
        }
    } else if (currentElem) {
        activeElement = currentElem;
    }

    if (key === 'Escape') {
        reset();
    } else if (!resultsAvailable || !inbox) {
        return;
    } else if (key === 'ArrowDown') {
        e.preventDefault();
        if (activeElement === sInput) {
            activeToggle(resList.firstChild.lastChild);
        } else if (activeElement.parentElement !== last) {
            activeToggle(activeElement.parentElement.nextSibling.lastChild);
        }
    } else if (key === 'ArrowUp') {
        e.preventDefault();
        if (activeElement.parentElement === first) {
            activeToggle(sInput);
        } else if (activeElement !== sInput) {
            activeToggle(activeElement.parentElement.previousSibling.lastChild);
        }
    } else if (key === 'ArrowRight') {
        activeElement.click();
    }
};
