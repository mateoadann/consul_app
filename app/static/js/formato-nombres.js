(() => {
  const examples = {
    paciente: { nombre: "Maria", apellido: "Lopez", apodo: "Mari" },
    profesional: { nombre: "Carla", apellido: "Garcia", apodo: "Dra. Car" },
  };

  function formatName(entity, key) {
    const nombre = entity.nombre;
    const apellido = entity.apellido;
    const apodo = entity.apodo || "";
    const inicial = apellido ? apellido[0] + "." : "";
    const fallback = (nombre + " " + inicial).trim();

    if (key === "nombre") return nombre;
    if (key === "nombre_apellido") return (nombre + " " + apellido).trim();
    if (key === "nombre_inicial") return fallback;
    if (key === "apodo") return apodo || fallback;
    if (key === "apodo_inicial") return apodo ? (apodo + " " + inicial).trim() : fallback;
    return fallback;
  }

  function updatePreview() {
    const fmtP = document.getElementById("fmt-paciente").value;
    const fmtR = document.getElementById("fmt-profesional").value;
    document.getElementById("preview-paciente").textContent = formatName(examples.paciente, fmtP);
    document.getElementById("preview-profesional").textContent = formatName(examples.profesional, fmtR);
  }

  document.getElementById("fmt-paciente").addEventListener("change", updatePreview);
  document.getElementById("fmt-profesional").addEventListener("change", updatePreview);
  updatePreview();
})();
