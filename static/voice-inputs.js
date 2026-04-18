(function initVoiceInputs() {
  const RecognitionCtor = window.SpeechRecognition || window.webkitSpeechRecognition;
  const enhancedFields = new WeakSet();
  let activeSession = null;

  function notify(message) {
    if (typeof window.pokazPowiadomienie === "function") {
      window.pokazPowiadomienie(message);
    }
  }

  function isEligibleField(element) {
    if (!(element instanceof HTMLElement)) {
      return false;
    }
    if (element.dataset.voiceDisabled === "true") {
      return false;
    }
    if (element.matches("textarea")) {
      return true;
    }
    if (!element.matches("input")) {
      return false;
    }
    const type = String(element.type || "text").toLowerCase();
    return ["text", "search", "email", "url", "tel"].includes(type);
  }

  function wrapField(field) {
    if (field.parentElement?.classList.contains("voice-field")) {
      return field.parentElement;
    }
    const wrapper = document.createElement("div");
    wrapper.className = "voice-field";
    field.parentNode?.insertBefore(wrapper, field);
    wrapper.appendChild(field);
    return wrapper;
  }

  function collectTranscript(event) {
    let transcript = "";
    for (let index = event.resultIndex; index < event.results.length; index += 1) {
      transcript += event.results[index][0]?.transcript || "";
    }
    return transcript.trim();
  }

  function dispatchFieldEvents(field) {
    field.dispatchEvent(new Event("input", { bubbles: true }));
    field.dispatchEvent(new Event("change", { bubbles: true }));
  }

  function setFieldValueWithTranscript(field, transcript, session) {
    const cleanTranscript = String(transcript || "").trim();
    if (!cleanTranscript) {
      return;
    }
    const before = session.baseValue.slice(0, session.selectionStart);
    const after = session.baseValue.slice(session.selectionEnd);
    const prefixSpacer = before && !/\s$/.test(before) ? " " : "";
    const suffixSpacer = after && !/^\s/.test(after) ? " " : "";
    const nextValue = `${before}${prefixSpacer}${cleanTranscript}${suffixSpacer}${after}`;
    field.value = nextValue;
    const caretPosition = (before + prefixSpacer + cleanTranscript).length;
    if (typeof field.setSelectionRange === "function") {
      field.setSelectionRange(caretPosition, caretPosition);
    }
    dispatchFieldEvents(field);
  }

  function cleanupSession() {
    if (!activeSession) {
      return;
    }
    activeSession.button.classList.remove("is-recording");
    activeSession.button.textContent = "Mic";
    activeSession.button.title = "Nagrywaj glosem";
    activeSession = null;
  }

  function stopActiveSession() {
    if (!activeSession) {
      return;
    }
    try {
      activeSession.recognition.stop();
    } catch (error) {
      cleanupSession();
    }
  }

  function startRecording(field, button) {
    if (!RecognitionCtor) {
      notify("Ta przegladarka nie obsluguje dyktowania glosowego.");
      return;
    }
    if (activeSession?.field === field) {
      stopActiveSession();
      return;
    }
    stopActiveSession();

    const recognition = new RecognitionCtor();
    const selectionStart = typeof field.selectionStart === "number" ? field.selectionStart : field.value.length;
    const selectionEnd = typeof field.selectionEnd === "number" ? field.selectionEnd : field.value.length;
    activeSession = {
      recognition,
      field,
      button,
      baseValue: field.value,
      selectionStart,
      selectionEnd,
    };

    recognition.lang = document.documentElement.lang === "pl" ? "pl-PL" : "en-US";
    recognition.continuous = false;
    recognition.interimResults = true;

    recognition.onstart = () => {
      button.classList.add("is-recording");
      button.textContent = "Stop";
      button.title = "Zatrzymaj nagrywanie";
      field.focus();
    };

    recognition.onresult = (event) => {
      if (!activeSession || activeSession.field !== field) {
        return;
      }
      setFieldValueWithTranscript(field, collectTranscript(event), activeSession);
    };

    recognition.onerror = (event) => {
      cleanupSession();
      if (event.error === "not-allowed" || event.error === "service-not-allowed") {
        notify("Przegladarka zablokowala dostep do mikrofonu.");
        return;
      }
      if (event.error === "no-speech" || event.error === "aborted") {
        return;
      }
      notify("Nie udalo sie rozpoznac dyktowania glosowego.");
    };

    recognition.onend = () => {
      cleanupSession();
    };

    try {
      recognition.start();
    } catch (error) {
      cleanupSession();
      notify("Nie udalo sie uruchomic mikrofonu w tej chwili.");
    }
  }

  function enhanceField(field) {
    if (!isEligibleField(field) || enhancedFields.has(field)) {
      return;
    }
    enhancedFields.add(field);
    const wrapper = wrapField(field);
    const button = document.createElement("button");
    button.type = "button";
    button.className = "secondary voice-field-button";
    button.textContent = "Mic";
    button.title = RecognitionCtor ? "Nagrywaj glosem" : "Dyktowanie glosowe nie jest dostepne";
    button.disabled = !RecognitionCtor;
    button.addEventListener("click", () => startRecording(field, button));
    wrapper.appendChild(button);
  }

  function enhanceAllFields(root = document) {
    root.querySelectorAll("input, textarea").forEach((field) => enhanceField(field));
  }

  enhanceAllFields();

  const observer = new MutationObserver((mutations) => {
    mutations.forEach((mutation) => {
      mutation.addedNodes.forEach((node) => {
        if (!(node instanceof HTMLElement)) {
          return;
        }
        if (node.matches?.("input, textarea")) {
          enhanceField(node);
          return;
        }
        enhanceAllFields(node);
      });
    });
  });

  observer.observe(document.body, { childList: true, subtree: true });
})();
