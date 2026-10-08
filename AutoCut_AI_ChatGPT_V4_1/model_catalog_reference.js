// Core v4.1 model-catalog behavior used by Auto Cut AI.
// Current Sign in with ChatGPT catalog: {models:[{slug,display_name,visibility}, ...]}.

function parseModelCatalog(obj) {
  var out = [], seen = {};
  function add(slug, display) {
    slug = String(slug || "").trim();
    if (!slug || seen[slug]) return;
    seen[slug] = true;
    out.push({ slug: slug, display_name: String(display || slug) });
  }

  if (obj && Array.isArray(obj.models)) {
    obj.models.forEach(function (m) {
      if (!m) return;
      if (m.visibility && String(m.visibility) !== "list") return;
      add(m.slug || m.id, m.display_name || m.name || m.slug || m.id);
    });
  }

  // Compatibility fallback only.
  if (!out.length && obj && Array.isArray(obj.data)) {
    obj.data.forEach(function (m) {
      if (!m) return;
      var id = String(m.slug || m.id || "");
      if (/(realtime|audio|image|tts|transcrib|search|embed)/i.test(id)) return;
      add(id, m.display_name || m.name || id);
    });
  }

  return out;
}

function chooseModel(models, requested) {
  models = models || [];
  if (requested && requested !== "Auto") {
    for (var i = 0; i < models.length; i++) {
      if (models[i].slug === requested) return requested;
    }
    return null;
  }
  return models.length ? models[0].slug : null;
}
