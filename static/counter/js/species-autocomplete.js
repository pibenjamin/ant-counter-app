(function () {
    const API_URL = "https://api.gbif.org/v1/species/suggest";

    var input = document.getElementById("id_species") || document.getElementById("species");
    if (!input) return;

    var container = input.parentElement;
    container.style.position = "relative";

    var dropdown = document.createElement("div");
    dropdown.id = "species-dropdown";
    dropdown.style.cssText =
        "position:absolute;top:100%;left:0;right:0;z-index:1000;" +
        "background:#fff;border:1px solid #ddd;border-radius:4px;" +
        "max-height:220px;overflow-y:auto;display:none;box-shadow:0 4px 12px rgba(0,0,0,0.15);";
    container.appendChild(dropdown);

    var selectedIndex = -1;
    var results = [];
    var debounceTimer = null;

    function closeDropdown() {
        dropdown.style.display = "none";
        selectedIndex = -1;
    }

    function selectItem(index) {
        if (index >= 0 && index < results.length) {
            var item = results[index];
            input.value = item.scientificName || item.canonicalName || item.species;
            closeDropdown();
        }
    }

    function highlightItem(index) {
        var items = dropdown.querySelectorAll("div");
        items.forEach(function (el, i) {
            el.style.background = i === index ? "#e9f5e9" : "";
        });
        selectedIndex = index;
    }

    function renderDropdown(data) {
        dropdown.innerHTML = "";
        results = (data || []).filter(function (item) {
            return item.family === "Formicidae";
        });

        if (results.length === 0) {
            var div = document.createElement("div");
            div.textContent = "Aucune fourmi trouvée";
            div.style.cssText = "padding:8px 12px;color:#999;font-size:13px;";
            dropdown.appendChild(div);
            dropdown.style.display = "block";
            return;
        }

        results.forEach(function (item, i) {
            var div = document.createElement("div");
            div.style.cssText =
                "padding:8px 12px;cursor:pointer;font-size:14px;border-bottom:1px solid #f0f0f0;";

            var name = item.scientificName || item.canonicalName || item.species || "";
            var authorDate = "";
            if (name && name.indexOf("(") > 0) {
                authorDate = name.substring(name.indexOf("("));
                name = name.substring(0, name.indexOf("(")).trim();
            }

            div.innerHTML =
                "<strong>" + escapeHtml(name) + "</strong>" +
                " <span style='color:#888;font-size:12px;'>" +
                escapeHtml(authorDate) + " " +
                "Formicidae</span>";

            div.addEventListener("click", function () { selectItem(i); });
            div.addEventListener("mouseenter", function () { highlightItem(i); });

            dropdown.appendChild(div);
        });

        dropdown.style.display = "block";
        selectedIndex = -1;
    }

    function fetchSpecies(query) {
        if (query.length < 2) return;

        var url = API_URL + "?q=" + encodeURIComponent(query) +
                  "&rank=SPECIES";

        fetch(url)
            .then(function (r) {
                if (!r.ok) throw new Error("HTTP " + r.status);
                return r.json();
            })
            .then(function (data) {
                if (data && data.length > 0) renderDropdown(data);
                else closeDropdown();
            })
            .catch(function () { closeDropdown(); });
    }

    function escapeHtml(str) {
        if (!str) return "";
        var d = document.createElement("div");
        d.textContent = str;
        return d.innerHTML;
    }

    input.addEventListener("input", function () {
        clearTimeout(debounceTimer);
        var val = input.value.trim();
        if (val.length < 2) { closeDropdown(); return; }
        debounceTimer = setTimeout(function () {
            fetchSpecies(val);
        }, 300);
    });

    input.addEventListener("keydown", function (e) {
        if (dropdown.style.display === "none") return;

        if (e.key === "ArrowDown") {
            e.preventDefault();
            highlightItem(Math.min(selectedIndex + 1, results.length - 1));
        } else if (e.key === "ArrowUp") {
            e.preventDefault();
            highlightItem(Math.max(selectedIndex - 1, 0));
        } else if (e.key === "Enter" || e.key === "Tab") {
            if (selectedIndex >= 0) {
                selectItem(selectedIndex);
                if (e.key === "Enter") e.preventDefault();
            }
        } else if (e.key === "Escape") {
            closeDropdown();
        }
    });

    input.addEventListener("blur", function () {
        setTimeout(closeDropdown, 200);
    });

    input.addEventListener("focus", function () {
        if (results.length > 0) dropdown.style.display = "block";
    });
})();
