(function () {
  const editorEl = document.getElementById("quill-editor");
  const form = document.getElementById("journal-form");
  const bodyInput = document.getElementById("body_html");

  if (!editorEl || !form || !bodyInput || typeof Quill === "undefined") {
    return;
  }

  const quill = new Quill(editorEl, {
    theme: "snow",
    placeholder: "Hoe voel je je vandaag? Wat ging goed, wat was lastig?",
    modules: {
      toolbar: [
        ["bold", "italic", "underline"],
        [{ list: "ordered" }, { list: "bullet" }],
        ["blockquote"],
        ["clean"],
      ],
    },
  });

  const initial = window.journalInitialContent || "";
  if (initial) {
    quill.root.innerHTML = initial;
  }

  form.addEventListener("submit", function () {
    bodyInput.value = quill.root.innerHTML;
  });
})();
