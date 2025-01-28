"use strict";


/**
 * A general lookup button, for images, sentences, etc.
 */
class LookupButton {

  /** State required by the buttons. */
  static TERM_FORM_CONTAINER = null;
  static TERM_DICTS = null;
  static LANG_ID = null;


  /** All LookupButtons created. */
  static all = [];

  constructor(frameName) {
    let createIFrame = function(name) {
      const f = document.createElement("iframe");
      f.name = name;
      f.src = "about:blank";
      f.classList.add("dictframe");
      return f;
    };

    this.dictID = null;
    this.is_active = false;
    this.contentLoaded = false;

    this.frame = createIFrame(frameName);
    this.frame.setAttribute("sandbox", "allow-same-origin allow-scripts");
    this.btn = document.createElement("button");
    this.btn.classList.add("dict-btn");
    this.btn.onclick = () => this.do_lookup();

    LookupButton.all.push(this);
  }

  /** Lookup. *************************/

  do_lookup() {
    throw new Error('Subclasses must override.');
  }

  /** Activate/deact. *************************/

  deactivate() {
    this.is_active = false;
    this.btn.classList.remove("dict-btn-active");
    this.frame.classList.remove("dict-active");
  }

  activate() {
    DictButton.all.forEach(button => button.deactivate());
    this.is_active = true;
    this.btn.classList.add("dict-btn-active");
    this.frame.classList.add("dict-active");
  }

};


/**
 * A general lookup button that's doesn't use dictionaries.
 * For buttons that get info about a term.
 * This content is never cached -- form values may change the search,
 * so it's fine to always reload.
 */
class GeneralLookupButton extends LookupButton {
  constructor(btn_id, btn_textContent, btn_title, btn_className, clickHandler) {
    super(`frame_for_${btn_id}`);

    const b = this.btn;
    b.setAttribute("id", btn_id);
    b.setAttribute("title", btn_title);
    b.textContent = btn_textContent;
    b.classList.add(btn_className);

    this.click_handler = clickHandler;
  }

  do_lookup() {
    this.click_handler(this.frame);
    this.activate();
  }

}  // end GeneralLookupButton


class SentenceLookupButton extends GeneralLookupButton {
  constructor() {
    let handler = function(iframe) {
      const txt = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
      // %E2%80%8B is the zero-width string.  The term is reparsed
      // on the server, so this doesn't need to be sent.
      const t = encodeURIComponent(txt).replaceAll('%E2%80%8B', '');
      const langid = `${LookupButton.LANG_ID ?? 0}`;
      if (langid == '0' || t == '')
        return;
      iframe.setAttribute("src", `/term/sentences/${LookupButton.LANG_ID}/${t}`);
    };

    super("sentences-btn", "Sentences", "See term usage", "dict-sentences-btn", handler);
  }
}


class ImageLookupButton extends GeneralLookupButton {
  constructor() {

    // Parents are in the tagify-managed #parentslist input box.
    let _get_parent_tag_values = function() {
      const pdata = LookupButton.TERM_FORM_CONTAINER.querySelector("#parentslist").value
      if ((pdata ?? '') == '')
        return [];
      return JSON.parse(pdata).map(e => e.value);
    };

    let handler = function(iframe) {
      const text = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
      const lang_id = LookupButton.LANG_ID;
      if (lang_id == null || lang_id == '' || parseInt(lang_id) == 0 || text == null || text == '') {
        alert('Please select a language and enter the term.');
        return;
      }
      let use_text = text;

      // If there is a single parent, use that as the basis of the lookup.
      const parents = _get_parent_tag_values();
      if (parents.length == 1)
        use_text = parents[0];

      const raw_bing_url = 'https://www.bing.com/images/search?q=[LUTE]&form=HDRSC2&first=1&tsc=ImageHoverTitle';
      const binghash = raw_bing_url.replace('https://www.bing.com/images/search?', '');
      const url = `/bing/search/${LookupButton.LANG_ID}/${encodeURIComponent(use_text)}/${encodeURIComponent(binghash)}`;

      iframe.setAttribute("src", url);
    };  // end handler

    super("dict-image-btn", null, "Lookup images", "dict-image-btn", handler);
  }
}


/**
 * A "dictionary button" to be shown in the UI.
 * Manages display state, loading and caching content.
 *
 * The class *could* be broken up into things like
 * PopupDictButton, EmbeddedDictButton, etc, but no need for that yet.
 */
class DictButton extends LookupButton {

  constructor(dictURL, frameName) {
    super(frameName);

    this.dictID = LookupButton.TERM_DICTS.indexOf(dictURL);
    if (this.dictID == -1) {
      console.log(`Error: Dict url ${dictURL} not found (??)`);
      return;
    }

    const url = dictURL.split("*").splice(-1)[0];

    this.label = (url.length <= 10) ? url : (url.slice(0, 10) + '...');

    // If the URL is a real url, get icon and label.
    let fimg = null;
    try {
      const urlObj = new URL(url);  // Throws if invalid.
      const domain = urlObj.hostname;
      this.label = domain.split("www.").splice(-1)[0];

      fimg = document.createElement("img");
      fimg.classList.add("dict-btn-fav-img");
      const favicon_src = `http://www.google.com/s2/favicons?domain=${domain}`;
      fimg.src = favicon_src;
    }
    catch(err) {}

    this.btn.textContent = this.label;

    // Must prepend after the textContent is set, or it is overwritten/lost.
    if (fimg != null)
      this.btn.prepend(fimg);

    this.btn.setAttribute("title", this.label);

    this.isExternal = (dictURL.charAt(0) == '*');
    if (this.isExternal) {
      const ext_img = document.createElement("img");
      ext_img.classList.add("dict-btn-external-img");
      this.btn.classList.add("dict-btn-external");
      this.btn.appendChild(ext_img);
    }
  }

  /** LOOKUPS *************************/

  do_lookup() {
    const dicturl = LookupButton.TERM_DICTS[this.dictID];
    if (LookupButton.TERM_FORM_CONTAINER == null || dicturl == null)
      return;
    const term = LookupButton.TERM_FORM_CONTAINER.querySelector("#text").value;
    if (this.isExternal) {
      this._load_popup(dicturl, term);
    }
    else {
      this._load_frame(dicturl, term);
    }
    this.activate();
  }

  _get_lookup_url(dicturl, term) {
    let ret = dicturl;
    // Terms are saved with zero-width space between each token;
    // remove that for dict searches.
    const zeroWidthSpace = '\u200b';
    const sqlZWS = '%E2%80%8B';
    const cleantext = term.
          replaceAll(zeroWidthSpace, '').
          replace(/\s+/g, ' ');
    const searchterm = encodeURIComponent(cleantext).
          replaceAll(sqlZWS, '');
    ret = ret.replace('[LUTE]', searchterm);
    ret = ret.replace('###', searchterm);  // TODO remove_old_###_placeholder
    return ret;
  }

  _load_popup(url, term) {
    if ((url ?? "") == "")
      return;
    if (url[0] == "*")  // Should be true!
      url = url.slice(1);
    const lookup_url = this._get_lookup_url(url, term);
    let settings = 'width=800, height=600, scrollbars=yes, menubar=no, resizable=yes, status=no'
    if (LUTE_USER_SETTINGS.open_popup_in_new_tab)
      settings = null;
    window.open(lookup_url, 'otherwin', settings);
  }

  _load_frame(dicturl, text) {
    if (this.isExternal || this.dictID == null) {
      return;
    }
    if (this.contentLoaded) {
      console.log(`${this.label} content already loaded.`);
      return;
    }

    let url = this._get_lookup_url(dicturl, text);

    const is_bing_image_search = (dicturl.indexOf('www.bing.com/images') != -1);
    if (is_bing_image_search) {
      // TODO handle_image_lookup_separately: don't mix term lookups with image lookups.
      let use_text = text;
      const binghash = dicturl.replace('https://www.bing.com/images/search?', '');
      url = `/bing/search/${LookupButton.LANG_ID}/${encodeURIComponent(use_text)}/${encodeURIComponent(binghash)}`;
    }

    this.frame.setAttribute("src", url);
    this.contentLoaded = true;
  }

}  // end DictButton


/**
 * Load excess buttons in a separate div.
 */
function _create_dict_dropdown_div(buttons_in_list) {
  // div containing all the buttons_in_list.
  const list_div = document.createElement("div");
  list_div.setAttribute("id", "dict-list-container");
  list_div.classList.add("dict-list-hide");
  buttons_in_list.forEach(button => {
    button.btn.classList.remove("dict-btn");
    button.btn.classList.add("dict-menu-item");
    list_div.appendChild(button.btn);
  });

  // Top level button to show/hide the list.
  const btn = document.createElement("button");
  btn.classList.add("dict-btn", "dict-btn-select");
  btn.innerHTML = "&hellip; &#9660;"
  btn.setAttribute("title", "More dictionaries");
  btn.addEventListener("click", (e) => {
    list_div.classList.toggle("dict-list-hide");
  });

  const menu_div = document.createElement("div");
  menu_div.setAttribute("id", "dict-menu-container");
  menu_div.appendChild(list_div);
  menu_div.appendChild(btn);
  menu_div.addEventListener("mouseleave", () => {
    list_div.classList.add("dict-list-hide");
  });

  return menu_div;
}

/**
 * Create all buttons.
 */
function createLookupButtons(tab_count = 5) {
  let destroy_existing_dictTab_controls = function() {
    document.querySelectorAll(".dict-btn").forEach(item => item.remove())
    document.querySelectorAll(".dictframe").forEach(item => item.remove())
    const el = document.getElementById("dict-menu-container");
    if (el)
      el.remove();
  }
  destroy_existing_dictTab_controls();
  LookupButton.all = [];

  if (LookupButton.TERM_DICTS.length <= 0) return;

  // const dev_hack_add_dicts = Array.from({ length: 5 }, (_, i) => `a${i}`);
  // LookupButton.TERM_DICTS.push(...dev_hack_add_dicts);

  if (tab_count == (LookupButton.TERM_DICTS.length - 1)) {
    // Don't bother making a list with a single item.
    tab_count += 1;
  }

  // Make all DictButtons, which loads LookupButton.all.
  LookupButton.TERM_DICTS.forEach((dict, index) => { new DictButton(dict,`dict${index}`); });
  const tab_buttons = LookupButton.all.slice(0, tab_count);
  const list_buttons = LookupButton.all.slice(tab_count);

  // Add elements to container.
  const container = document.getElementById("dicttabslayout");
  let grid_col_count = tab_buttons.length;
  tab_buttons.forEach(button => container.appendChild(button.btn));
  if (list_buttons.length > 0) {
    const dropdown_div = _create_dict_dropdown_div(list_buttons);
    container.appendChild(dropdown_div);
    grid_col_count += 1;
  }
  container.style.gridTemplateColumns = `repeat(${grid_col_count}, minmax(2rem, 8rem))`;

  const first_button = LookupButton.all[0];
  if (first_button) {
    first_button.activate();
    first_button.do_lookup();
  }

  for (let b of [new SentenceLookupButton(), new ImageLookupButton()])
    document.getElementById("dicttabsstatic").appendChild(b.btn);

  const dictframes = document.getElementById("dictframes");
  LookupButton.all.forEach((button) => { dictframes.appendChild(button.frame); });
}


function loadDictionaries() {
  const dictContainer = document.querySelector(".dictcontainer");
  dictContainer.style.display = "flex";
  dictContainer.style.flexDirection = "column";
  LookupButton.all.forEach(button => button.contentLoaded = false);
  const active_button = LookupButton.all.find(button => button.is_active);
  if (active_button) {
    active_button.do_lookup();
  }
}
