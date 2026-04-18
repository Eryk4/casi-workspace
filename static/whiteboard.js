(function () {
  const WHITEBOARD_POLL_INTERVAL_MS = 4000;
  const WHITEBOARD_POINT_DISTANCE_THRESHOLD = 0.002;
  const WHITEBOARD_IMAGE_MIN_RATIO = 0.03;
  const WHITEBOARD_IMAGE_HANDLE_RADIUS = 16;
  const WHITEBOARD_IMAGE_ROTATE_HANDLE_OFFSET = 34;

  function ensureWhiteboardState() {
    if (!stan.whiteboard) {
      stan.whiteboard = {
        events: [],
        pendingStrokes: [],
        currentStroke: null,
        scopeOrganizationId: null,
        latestEventId: 0,
        lastClearedEventId: 0,
        isSaving: false,
        isUploadingImage: false,
        boardVisible: true,
        drawingEnabled: false,
        imageEditEnabled: false,
        eraserEnabled: false,
        interfaceHidden: false,
        toolbarOpen: false,
        lastError: "",
        updatedAt: "",
        updatedBy: "",
        selectedImageEventId: null,
        imageTransformDraft: null,
        imageInteraction: null,
        isUpdatingImage: false,
        pollTimeoutId: null,
        domBound: false,
        canvasRatio: 1,
        imageCache: {},
      };
    }
    return stan.whiteboard;
  }

  function getWhiteboardDom() {
    return {
      layer: document.getElementById("whiteboard-layer"),
      canvas: document.getElementById("whiteboard-canvas"),
      launcher: document.getElementById("whiteboard-launcher"),
      toolbar: document.getElementById("whiteboard-toolbar"),
      organizationLabel: document.getElementById("whiteboard-organization-label"),
      hideToolbarButton: document.getElementById("whiteboard-hide-toolbar"),
      toggleBoardButton: document.getElementById("whiteboard-toggle-board"),
      toggleDrawingButton: document.getElementById("whiteboard-toggle-drawing"),
      toggleEraserButton: document.getElementById("whiteboard-toggle-eraser"),
      toggleImageEditButton: document.getElementById("whiteboard-toggle-image-edit"),
      toggleInterfaceButton: document.getElementById("whiteboard-toggle-interface"),
      addImageButton: document.getElementById("whiteboard-add-image"),
      imageInput: document.getElementById("whiteboard-image-input"),
      colorInput: document.getElementById("whiteboard-color"),
      widthInput: document.getElementById("whiteboard-width"),
      saveNowButton: document.getElementById("whiteboard-save-now"),
      clearButton: document.getElementById("whiteboard-clear"),
      statusBox: document.getElementById("whiteboard-status"),
    };
  }

  function getWhiteboardInteractiveTarget(element) {
    if (!element || typeof element.closest !== "function") {
      return null;
    }
    return element.closest(
      [
        "button",
        "input",
        "select",
        "textarea",
        "label",
        "a",
        "[role='button']",
        "[contenteditable='true']",
        ".whiteboard-toolbar",
        ".whiteboard-launcher",
        ".toast",
        ".auth-screen",
        ".clickable",
        ".planner-card",
        ".search-result-item",
        ".search-ai-source",
        ".knowledge-question-chip",
        ".knowledge-doc-item",
        ".scope-option",
        ".mini-action",
      ].join(", ")
    );
  }

  function shouldHandleWhiteboardPointerEvent(event) {
    if (!event) {
      return false;
    }
    const state = ensureWhiteboardState();
    if (!state.drawingEnabled || !isWhiteboardVisible()) {
      return false;
    }
    const target = event.target instanceof Element ? event.target : null;
    return !getWhiteboardInteractiveTarget(target);
  }

  function getWhiteboardScopeOrganizationId() {
    if (!stan.biezacyUzytkownik) {
      return null;
    }
    if (typeof czyGlobalnyAdministrator === "function" && czyGlobalnyAdministrator()) {
      const selectedId = Number(stan.wybranaOrganizacjaId || 0);
      return selectedId > 0 ? selectedId : null;
    }
    const organizationId = Number(stan.biezacyUzytkownik.organization_id || 0);
    return organizationId > 0 ? organizationId : null;
  }

  function getWhiteboardScopeLabel() {
    const scopeOrganization = typeof pobierzAktywnaOrganizacje === "function" ? pobierzAktywnaOrganizacje() : null;
    if (scopeOrganization?.name) {
      return scopeOrganization.name;
    }
    if (stan.biezacyUzytkownik?.organization_name) {
      return stan.biezacyUzytkownik.organization_name;
    }
    return "Brak wybranej organizacji";
  }

  function canUseWhiteboard() {
    return Boolean(stan.biezacyUzytkownik && getWhiteboardScopeOrganizationId());
  }

  function isWhiteboardVisible() {
    const state = ensureWhiteboardState();
    return canUseWhiteboard() && state.boardVisible;
  }

  function isWhiteboardInteractionMode() {
    const state = ensureWhiteboardState();
    return isWhiteboardVisible() && (state.drawingEnabled || state.imageEditEnabled);
  }

  function canClearWhiteboard() {
    return typeof czyMoznaZapisywac === "function" ? czyMoznaZapisywac() : false;
  }

  function setWhiteboardStatus(message) {
    const dom = getWhiteboardDom();
    if (dom.statusBox) {
      dom.statusBox.textContent = message;
    }
  }

  function buildWhiteboardStatusMessage() {
    const state = ensureWhiteboardState();
    const pendingCount = state.pendingStrokes.length + (state.currentStroke ? 1 : 0);

    if (!stan.biezacyUzytkownik) {
      return "Zaloguj sie, aby korzystac ze wspolnej tablicy organizacji.";
    }
    if (!canUseWhiteboard()) {
      return "Wybierz konkretna organizacje, aby uruchomic wspolna tablice.";
    }
    if (!state.boardVisible) {
      return "Tablica jest wylaczona. Mozesz wlaczyc ja ponownie i wrocic do zwyklego tla aplikacji.";
    }
    if (state.lastError) {
      return `Blad zapisu tablicy: ${state.lastError}`;
    }
    if (state.isUploadingImage) {
      return "Dodawanie obrazka na wspolna tablice...";
    }
    if (state.isUpdatingImage) {
      return "Zapisywanie zmian obrazka na wspolnej tablicy...";
    }
    if (state.imageInteraction) {
      return "Przesun, zmien rozmiar albo obroc zaznaczony obrazek, a potem pusc wskaznik.";
    }
    if (state.imageEditEnabled && state.selectedImageEventId) {
      return "Obrazek jest zaznaczony. Przeciagnij srodek, aby go przesunac, albo zlap uchwyt, by zmienic rozmiar lub obrocic.";
    }
    if (state.imageEditEnabled) {
      return "Kliknij obrazek, aby go zaznaczyc. Potem uzyj uchwytow do zmiany rozmiaru i obrotu.";
    }
    if (state.isSaving) {
      return `Zapisywanie tablicy... oczekuje ${pendingCount} lokalnych ruchow.`;
    }
    if (pendingCount > 0) {
      return `Lokalne ruchy oczekuja na zapis: ${pendingCount}.`;
    }
    if (state.updatedAt) {
      const updatedAt = typeof formatujDateCzas === "function" ? formatujDateCzas(state.updatedAt) : state.updatedAt;
      const updatedBy = state.updatedBy ? ` przez ${state.updatedBy}` : "";
      return `Ostatnia zmiana: ${updatedAt}${updatedBy}. Odswiezanie wspolne co ${Math.round(
        WHITEBOARD_POLL_INTERVAL_MS / 1000
      )} s.`;
    }
    return "Tablica gotowa. Zmiany innych osob odswiezaja sie automatycznie co kilka sekund.";
  }

  function renderWhiteboardUi() {
    const state = ensureWhiteboardState();
    const dom = getWhiteboardDom();
    if (!dom.layer || !dom.canvas || !dom.launcher || !dom.toolbar) {
      return;
    }

    const available = canUseWhiteboard();
    if (!available) {
      state.toolbarOpen = false;
      state.boardVisible = true;
      state.drawingEnabled = false;
      state.imageEditEnabled = false;
      state.eraserEnabled = false;
      state.interfaceHidden = false;
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
    }

    const boardVisible = available && state.boardVisible;
    if (!boardVisible) {
      state.drawingEnabled = false;
      state.imageEditEnabled = false;
      state.interfaceHidden = false;
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
    }

    dom.layer.classList.toggle("hidden", !boardVisible);
    dom.layer.classList.toggle("is-drawing", boardVisible && state.drawingEnabled);
    dom.layer.classList.toggle("is-editing-images", boardVisible && state.imageEditEnabled);
    dom.layer.classList.toggle("is-manipulating", Boolean(state.imageInteraction));
    dom.launcher.classList.toggle("hidden", !stan.biezacyUzytkownik);
    dom.launcher.classList.toggle("is-active", state.toolbarOpen);
    dom.launcher.classList.toggle("is-drawing", boardVisible && state.drawingEnabled);
    dom.launcher.classList.toggle("is-disabled", !available || (available && !boardVisible));
    dom.launcher.textContent = "Tablica";
    dom.toolbar.classList.toggle("hidden", !available || !state.toolbarOpen);
    document.body.classList.toggle(
      "whiteboard-drawing-mode",
      boardVisible && (state.drawingEnabled || state.imageEditEnabled)
    );
    document.body.classList.toggle("whiteboard-interface-hidden", boardVisible && state.interfaceHidden);

    if (dom.organizationLabel) {
      dom.organizationLabel.textContent = available
        ? `Zakres tablicy: ${getWhiteboardScopeLabel()}`
        : "Wybierz organizacje, aby pracowac na wspolnej tablicy.";
    }

    if (dom.toggleBoardButton) {
      dom.toggleBoardButton.textContent = boardVisible ? "Wyłącz tablicę" : "Włącz tablicę";
      dom.toggleBoardButton.classList.toggle("is-active", boardVisible);
      dom.toggleBoardButton.disabled = !available;
    }
    if (dom.toggleDrawingButton) {
      dom.toggleDrawingButton.textContent = state.drawingEnabled ? "Zakoncz rysowanie" : "Wlacz rysowanie";
      dom.toggleDrawingButton.classList.toggle("is-active", state.drawingEnabled);
      dom.toggleDrawingButton.disabled = !boardVisible;
    }
    if (dom.toggleImageEditButton) {
      dom.toggleImageEditButton.textContent = state.imageEditEnabled ? "Zakoncz edycje obrazkow" : "Edytuj obrazki";
      dom.toggleImageEditButton.classList.toggle("is-active", state.imageEditEnabled);
      dom.toggleImageEditButton.disabled = !boardVisible || state.isUploadingImage || state.isUpdatingImage;
    }
    if (dom.toggleEraserButton) {
      dom.toggleEraserButton.textContent = state.eraserEnabled ? "Marker" : "Gumka";
      dom.toggleEraserButton.classList.toggle("is-active", state.eraserEnabled);
      dom.toggleEraserButton.disabled = !boardVisible || state.imageEditEnabled;
    }
    if (dom.toggleInterfaceButton) {
      dom.toggleInterfaceButton.textContent = state.interfaceHidden ? "Pokaż interfejs" : "Ukryj interfejs";
      dom.toggleInterfaceButton.classList.toggle("is-active", state.interfaceHidden);
      dom.toggleInterfaceButton.disabled = !boardVisible;
    }
    if (dom.addImageButton) {
      dom.addImageButton.disabled = !boardVisible || state.isUploadingImage;
      dom.addImageButton.textContent = state.isUploadingImage ? "Dodawanie..." : "Dodaj obrazek";
    }
    if (dom.imageInput) {
      dom.imageInput.disabled = !boardVisible || state.isUploadingImage;
    }
    if (dom.colorInput) {
      dom.colorInput.disabled = !boardVisible;
    }
    if (dom.widthInput) {
      dom.widthInput.disabled = !boardVisible;
    }
    if (dom.saveNowButton) {
      dom.saveNowButton.disabled = !boardVisible || state.isSaving || state.pendingStrokes.length === 0;
    }
    if (dom.clearButton) {
      dom.clearButton.disabled = !boardVisible || !canClearWhiteboard() || state.isSaving;
    }

    if (dom.canvas) {
      dom.canvas.style.pointerEvents = boardVisible && (state.drawingEnabled || state.imageEditEnabled) ? "auto" : "none";
    }

    setWhiteboardStatus(buildWhiteboardStatusMessage());
  }

  function clearWhiteboardCanvas() {
    const { canvas } = getWhiteboardDom();
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);
  }

  function resizeWhiteboardCanvas() {
    const state = ensureWhiteboardState();
    const { canvas } = getWhiteboardDom();
    if (!canvas) {
      return;
    }

    const ratio = Math.max(1, window.devicePixelRatio || 1);
    const width = Math.max(1, Math.floor(window.innerWidth));
    const height = Math.max(1, Math.floor(window.innerHeight));

    if (canvas.width === Math.floor(width * ratio) && canvas.height === Math.floor(height * ratio)) {
      renderWhiteboardCanvas();
      return;
    }

    canvas.width = Math.floor(width * ratio);
    canvas.height = Math.floor(height * ratio);
    canvas.style.width = `${width}px`;
    canvas.style.height = `${height}px`;

    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }
    context.setTransform(ratio, 0, 0, ratio, 0, 0);
    state.canvasRatio = ratio;
    renderWhiteboardCanvas();
  }

  function denormalizeWhiteboardPoint(point) {
    const { canvas } = getWhiteboardDom();
    const width = canvas?.clientWidth || window.innerWidth || 1;
    const height = canvas?.clientHeight || window.innerHeight || 1;
    return {
      x: Number(point?.x || 0) * width,
      y: Number(point?.y || 0) * height,
    };
  }

  function denormalizeWhiteboardImageRect(imagePayload) {
    const { canvas } = getWhiteboardDom();
    const width = canvas?.clientWidth || window.innerWidth || 1;
    const height = canvas?.clientHeight || window.innerHeight || 1;
    const normalizedWidth = Math.max(0.01, Math.min(1, Number(imagePayload?.width || 0.32)));
    const normalizedHeight = Math.max(0.01, Math.min(1, Number(imagePayload?.height || 0.24)));
    const normalizedX = Math.max(0, Math.min(1 - normalizedWidth, Number(imagePayload?.x || 0)));
    const normalizedY = Math.max(0, Math.min(1 - normalizedHeight, Number(imagePayload?.y || 0)));
    const rotationDeg = Number(imagePayload?.rotation_deg || 0);
    return {
      x: normalizedX * width,
      y: normalizedY * height,
      width: normalizedWidth * width,
      height: normalizedHeight * height,
      rotationDeg: Number.isFinite(rotationDeg) ? rotationDeg : 0,
    };
  }

  function normalizeWhiteboardImagePayload(imagePayload, fallbackImageEventId) {
    const imageEventId = Number(imagePayload?.image_event_id || fallbackImageEventId || 0);
    return {
      image_event_id: imageEventId,
      file_name: String(imagePayload?.file_name || ""),
      mime_type: String(imagePayload?.mime_type || ""),
      image_link: String(imagePayload?.image_link || ""),
      image_storage_key: String(imagePayload?.image_storage_key || ""),
      x: normalizeWhiteboardRatio(imagePayload?.x, 0, 1),
      y: normalizeWhiteboardRatio(imagePayload?.y, 0, 1),
      width: normalizeWhiteboardRatio(imagePayload?.width, WHITEBOARD_IMAGE_MIN_RATIO, 1),
      height: normalizeWhiteboardRatio(imagePayload?.height, WHITEBOARD_IMAGE_MIN_RATIO, 1),
      rotation_deg: Number.isFinite(Number(imagePayload?.rotation_deg || 0))
        ? Number(Number(imagePayload?.rotation_deg || 0).toFixed(3))
        : 0,
    };
  }

  function getWhiteboardImageCenter(imagePayload) {
    const rect = denormalizeWhiteboardImageRect(imagePayload);
    return {
      x: rect.x + rect.width / 2,
      y: rect.y + rect.height / 2,
    };
  }

  function degreesToRadians(value) {
    return (Number(value || 0) * Math.PI) / 180;
  }

  function normalizeRotationDegrees(value) {
    let nextValue = Number(value || 0);
    if (!Number.isFinite(nextValue)) {
      return 0;
    }
    nextValue %= 360;
    if (nextValue > 180) {
      nextValue -= 360;
    }
    if (nextValue < -180) {
      nextValue += 360;
    }
    return Number(nextValue.toFixed(3));
  }

  function rotateWhiteboardPoint(point, center, angleRadians) {
    const deltaX = point.x - center.x;
    const deltaY = point.y - center.y;
    const cosAngle = Math.cos(angleRadians);
    const sinAngle = Math.sin(angleRadians);
    return {
      x: center.x + deltaX * cosAngle - deltaY * sinAngle,
      y: center.y + deltaX * sinAngle + deltaY * cosAngle,
    };
  }

  function getWhiteboardImageLocalPoint(point, imagePayload) {
    const rect = denormalizeWhiteboardImageRect(imagePayload);
    const center = getWhiteboardImageCenter(imagePayload);
    const unrotated = rotateWhiteboardPoint(point, center, -degreesToRadians(rect.rotationDeg));
    return {
      x: unrotated.x - center.x,
      y: unrotated.y - center.y,
      rect,
      center,
    };
  }

  function isPointInsideWhiteboardImage(point, imagePayload) {
    const localPoint = getWhiteboardImageLocalPoint(point, imagePayload);
    return (
      Math.abs(localPoint.x) <= localPoint.rect.width / 2 &&
      Math.abs(localPoint.y) <= localPoint.rect.height / 2
    );
  }

  function getWhiteboardImageControls(imagePayload) {
    const rect = denormalizeWhiteboardImageRect(imagePayload);
    const center = getWhiteboardImageCenter(imagePayload);
    const angleRadians = degreesToRadians(rect.rotationDeg);
    const rotatePoint = (x, y) => rotateWhiteboardPoint({ x: center.x + x, y: center.y + y }, center, angleRadians);
    const topCenter = rotatePoint(0, -rect.height / 2);
    return {
      rect,
      center,
      resizeHandle: rotatePoint(rect.width / 2, rect.height / 2),
      rotateHandle: rotatePoint(0, -rect.height / 2 - WHITEBOARD_IMAGE_ROTATE_HANDLE_OFFSET),
      topCenter,
      corners: [
        rotatePoint(-rect.width / 2, -rect.height / 2),
        rotatePoint(rect.width / 2, -rect.height / 2),
        rotatePoint(rect.width / 2, rect.height / 2),
        rotatePoint(-rect.width / 2, rect.height / 2),
      ],
    };
  }

  function buildRenderableWhiteboardItems() {
    const state = ensureWhiteboardState();
    const renderItems = [];
    const events = Array.isArray(state.events) ? state.events : [];

    events.forEach((event) => {
      if (event.event_type === "clear") {
        renderItems.length = 0;
        return;
      }
      if (event.event_type === "stroke") {
        renderItems.push({ kind: "stroke", payload: event.payload });
        return;
      }
      if (event.event_type === "image") {
        renderItems.push({
          kind: "image",
          imageEventId: Number(event.whiteboard_event_id || 0),
          payload: normalizeWhiteboardImagePayload(event.payload, event.whiteboard_event_id),
        });
        return;
      }
      if (event.event_type === "image_transform") {
        const targetImageEventId = Number(event.payload?.image_event_id || 0);
        if (!targetImageEventId) {
          return;
        }
        const targetItem = [...renderItems]
          .reverse()
          .find((item) => item.kind === "image" && Number(item.imageEventId || 0) === targetImageEventId);
        if (!targetItem) {
          return;
        }
        targetItem.payload = normalizeWhiteboardImagePayload(
          {
            ...targetItem.payload,
            ...event.payload,
            image_event_id: targetImageEventId,
          },
          targetImageEventId
        );
      }
    });

    if (state.imageTransformDraft) {
      const targetImageEventId = Number(state.imageTransformDraft.image_event_id || 0);
      const targetItem = [...renderItems]
        .reverse()
        .find((item) => item.kind === "image" && Number(item.imageEventId || 0) === targetImageEventId);
      if (targetItem) {
        targetItem.payload = normalizeWhiteboardImagePayload(state.imageTransformDraft, targetImageEventId);
      }
    }

    return renderItems;
  }

  function getRenderableWhiteboardImages() {
    return buildRenderableWhiteboardItems().filter((item) => item.kind === "image");
  }

  function clearWhiteboardImageCache() {
    const state = ensureWhiteboardState();
    Object.values(state.imageCache || {}).forEach((entry) => {
      if (entry?.objectUrl) {
        try {
          URL.revokeObjectURL(entry.objectUrl);
        } catch (error) {
          // ignore URL cleanup failures
        }
      }
    });
    state.imageCache = {};
  }

  function getWhiteboardImageCacheEntry(src) {
    if (!src) {
      return null;
    }
    const state = ensureWhiteboardState();
    if (state.imageCache[src]) {
      return state.imageCache[src];
    }

    const image = new Image();
    const entry = {
      status: "loading",
      image,
      objectUrl: null,
    };
    state.imageCache[src] = entry;

    image.decoding = "async";
    image.onload = () => {
      entry.status = "ready";
      renderWhiteboardCanvas();
    };
    image.onerror = () => {
      entry.status = "error";
      if (entry.objectUrl) {
        try {
          URL.revokeObjectURL(entry.objectUrl);
        } catch (error) {
          // ignore URL cleanup failures
        }
        entry.objectUrl = null;
      }
      renderWhiteboardCanvas();
    };
    fetch(src, { credentials: "same-origin" })
      .then(async (response) => {
        if (!response.ok) {
          throw new Error(`Nie udalo sie pobrac obrazka (${response.status}).`);
        }
        const contentType = (response.headers.get("Content-Type") || "").toLowerCase();
        if (!contentType.startsWith("image/")) {
          throw new Error("Serwer nie zwrocil poprawnego obrazka.");
        }
        const blob = await response.blob();
        entry.objectUrl = URL.createObjectURL(blob);
        image.src = entry.objectUrl;
      })
      .catch(() => {
        entry.status = "error";
        renderWhiteboardCanvas();
      });
    return entry;
  }

  function drawWhiteboardImagePlaceholder(context, imagePayload, label) {
    const rect = denormalizeWhiteboardImageRect(imagePayload);
    const center = getWhiteboardImageCenter(imagePayload);
    context.save();
    context.translate(center.x, center.y);
    context.rotate(degreesToRadians(rect.rotationDeg));
    context.fillStyle = "rgba(255, 255, 255, 0.74)";
    context.strokeStyle = "rgba(15, 92, 144, 0.35)";
    context.lineWidth = 1.5;
    context.fillRect(-rect.width / 2, -rect.height / 2, rect.width, rect.height);
    context.strokeRect(-rect.width / 2, -rect.height / 2, rect.width, rect.height);
    context.fillStyle = "#0f5c90";
    context.font = "600 14px 'Segoe UI', Tahoma, sans-serif";
    context.textAlign = "center";
    context.textBaseline = "middle";
    context.fillText(label, 0, 0, Math.max(80, rect.width - 24));
    context.restore();
  }

  function drawWhiteboardImageSelection(context, imagePayload) {
    const state = ensureWhiteboardState();
    if (!state.imageEditEnabled) {
      return;
    }
    const controls = getWhiteboardImageControls(imagePayload);
    const angleRadians = degreesToRadians(controls.rect.rotationDeg);

    context.save();
    context.translate(controls.center.x, controls.center.y);
    context.rotate(angleRadians);
    context.strokeStyle = "rgba(37, 99, 235, 0.95)";
    context.lineWidth = 2;
    context.setLineDash([8, 6]);
    context.strokeRect(
      -controls.rect.width / 2,
      -controls.rect.height / 2,
      controls.rect.width,
      controls.rect.height
    );
    context.restore();

    context.save();
    context.strokeStyle = "rgba(37, 99, 235, 0.95)";
    context.lineWidth = 2;
    context.beginPath();
    context.moveTo(controls.topCenter.x, controls.topCenter.y);
    context.lineTo(controls.rotateHandle.x, controls.rotateHandle.y);
    context.stroke();

    [controls.resizeHandle, controls.rotateHandle].forEach((handle, index) => {
      context.beginPath();
      context.fillStyle = index === 0 ? "#ffffff" : "#dbeafe";
      context.strokeStyle = "rgba(37, 99, 235, 0.95)";
      context.lineWidth = 2;
      context.arc(handle.x, handle.y, WHITEBOARD_IMAGE_HANDLE_RADIUS, 0, Math.PI * 2);
      context.fill();
      context.stroke();
    });
    context.restore();
  }

  function drawWhiteboardImage(context, imagePayload, options = {}) {
    if (!context || !imagePayload?.image_link) {
      return;
    }

    const cacheEntry = getWhiteboardImageCacheEntry(imagePayload.image_link);
    if (!cacheEntry || cacheEntry.status === "loading") {
      drawWhiteboardImagePlaceholder(context, imagePayload, "Ladowanie obrazka");
      return;
    }
    if (cacheEntry.status === "error") {
      drawWhiteboardImagePlaceholder(context, imagePayload, "Blad obrazka");
      return;
    }

    const rect = denormalizeWhiteboardImageRect(imagePayload);
    const center = getWhiteboardImageCenter(imagePayload);
    context.save();
    context.translate(center.x, center.y);
    context.rotate(degreesToRadians(rect.rotationDeg));
    context.drawImage(cacheEntry.image, -rect.width / 2, -rect.height / 2, rect.width, rect.height);
    context.strokeStyle = "rgba(15, 23, 42, 0.16)";
    context.lineWidth = 1;
    context.strokeRect(-rect.width / 2, -rect.height / 2, rect.width, rect.height);
    context.restore();
    if (options.selected) {
      drawWhiteboardImageSelection(context, imagePayload);
    }
  }

  function drawWhiteboardStroke(context, stroke) {
    if (!context || !stroke || !Array.isArray(stroke.points) || stroke.points.length === 0) {
      return;
    }

    const width = Number(stroke.width || 4);
    const points = stroke.points.map((point) => denormalizeWhiteboardPoint(point));
    context.save();
    context.lineCap = "round";
    context.lineJoin = "round";
    context.lineWidth = width;
    context.strokeStyle = stroke.color || "#0f5c90";
    context.fillStyle = stroke.color || "#0f5c90";
    context.globalCompositeOperation = stroke.tool === "eraser" ? "destination-out" : "source-over";

    if (points.length === 1) {
      context.beginPath();
      context.arc(points[0].x, points[0].y, width / 2, 0, Math.PI * 2);
      context.fill();
      context.restore();
      return;
    }

    context.beginPath();
    context.moveTo(points[0].x, points[0].y);
    for (let index = 1; index < points.length; index += 1) {
      context.lineTo(points[index].x, points[index].y);
    }
    context.stroke();
    context.restore();
  }

  function renderWhiteboardCanvas() {
    const state = ensureWhiteboardState();
    const { canvas } = getWhiteboardDom();
    if (!canvas) {
      return;
    }
    const context = canvas.getContext("2d");
    if (!context) {
      return;
    }

    context.clearRect(0, 0, canvas.clientWidth, canvas.clientHeight);

    let selectedImageVisible = false;
    buildRenderableWhiteboardItems().forEach((item) => {
      if (item.kind === "image") {
        const isSelected = Number(state.selectedImageEventId || 0) === Number(item.imageEventId || 0);
        if (isSelected) {
          selectedImageVisible = true;
        }
        drawWhiteboardImage(context, item.payload, { selected: isSelected });
        return;
      }
      drawWhiteboardStroke(context, item.payload);
    });

    if (!selectedImageVisible) {
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
    }

    state.pendingStrokes.forEach((stroke) => drawWhiteboardStroke(context, stroke));
    if (state.currentStroke) {
      drawWhiteboardStroke(context, state.currentStroke);
    }
  }

  function normalizeWhiteboardEvent(rawEvent) {
    return {
      whiteboard_event_id: Number(rawEvent?.whiteboard_event_id || 0),
      event_type: String(rawEvent?.event_type || ""),
      payload: rawEvent?.payload || {},
      created_at: rawEvent?.created_at || "",
      actor_label: rawEvent?.actor_label || "",
      created_by_user_id:
        rawEvent?.created_by_user_id === null || rawEvent?.created_by_user_id === undefined
          ? null
          : Number(rawEvent.created_by_user_id),
    };
  }

  function mergeWhiteboardEvents(events, replaceAll) {
    const state = ensureWhiteboardState();
    let nextEvents = replaceAll ? [] : Array.from(state.events || []);
    let knownIds = new Set(nextEvents.map((event) => Number(event.whiteboard_event_id || 0)));

    (events || []).forEach((rawEvent) => {
      const event = normalizeWhiteboardEvent(rawEvent);
      const eventId = Number(event.whiteboard_event_id || 0);
      if (!eventId || knownIds.has(eventId)) {
        return;
      }
      if (event.event_type === "clear") {
        nextEvents = [];
        knownIds = new Set();
      }
      nextEvents.push(event);
      knownIds.add(eventId);
    });

    state.events = nextEvents;
  }

  function applyWhiteboardPayload(payload) {
    const state = ensureWhiteboardState();
    const replaceAll = payload?.mode === "full";
    mergeWhiteboardEvents(payload?.events || [], replaceAll);
    state.latestEventId = Number(payload?.latest_event_id || state.latestEventId || 0);
    state.lastClearedEventId = Number(payload?.last_cleared_event_id || 0);
    state.updatedAt = payload?.updated_at || state.updatedAt || "";
    state.updatedBy = payload?.updated_by || state.updatedBy || "";
    renderWhiteboardCanvas();
    renderWhiteboardUi();
  }

  async function savePendingWhiteboardStrokes(showErrorToast) {
    const state = ensureWhiteboardState();
    if (state.isSaving || state.pendingStrokes.length === 0 || !canUseWhiteboard()) {
      renderWhiteboardUi();
      return;
    }

    const strokesToSave = state.pendingStrokes.slice();
    state.isSaving = true;
    state.lastError = "";
    renderWhiteboardUi();

    try {
      const payload = await api(zbudujAdresZOrganizacja("/api/whiteboard/events"), {
        method: "POST",
        body: JSON.stringify({ strokes: strokesToSave }),
      });
      state.pendingStrokes.splice(0, strokesToSave.length);
      applyWhiteboardPayload(payload);
      state.lastError = "";
    } catch (error) {
      state.lastError = error.message;
      if (showErrorToast && typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie(error.message);
      }
    } finally {
      state.isSaving = false;
      renderWhiteboardUi();
      renderWhiteboardCanvas();
    }

    if (!state.isSaving && state.pendingStrokes.length > 0 && !state.lastError) {
      void savePendingWhiteboardStrokes(false);
    }
  }

  function queueWhiteboardStroke(stroke) {
    const state = ensureWhiteboardState();
    state.pendingStrokes.push(stroke);
    state.lastError = "";
    renderWhiteboardUi();
    renderWhiteboardCanvas();
    void savePendingWhiteboardStrokes(false);
  }

  function normalizeWhiteboardRatio(value, minimum, maximum) {
    const numericValue = Number(value || 0);
    if (!Number.isFinite(numericValue)) {
      return minimum;
    }
    return Math.max(minimum, Math.min(maximum, Number(numericValue.toFixed(6))));
  }

  function getWhiteboardCanvasPoint(event) {
    const { canvas } = getWhiteboardDom();
    if (!canvas) {
      return { x: 0, y: 0 };
    }
    const rect = canvas.getBoundingClientRect();
    return {
      x: event.clientX - rect.left,
      y: event.clientY - rect.top,
    };
  }

  function findWhiteboardImageHit(point) {
    const state = ensureWhiteboardState();
    const images = getRenderableWhiteboardImages().slice().reverse();
    const selectedImageEventId = Number(state.selectedImageEventId || 0);
    const selectedImage = selectedImageEventId
      ? images.find((item) => Number(item.imageEventId || item.payload?.image_event_id || 0) === selectedImageEventId)
      : null;

    if (selectedImage) {
      const selectedPayload = selectedImage.payload;
      const controls = getWhiteboardImageControls(selectedPayload);
      if (Math.hypot(point.x - controls.rotateHandle.x, point.y - controls.rotateHandle.y) <= WHITEBOARD_IMAGE_HANDLE_RADIUS + 6) {
        return { mode: "rotate", payload: selectedPayload };
      }
      if (Math.hypot(point.x - controls.resizeHandle.x, point.y - controls.resizeHandle.y) <= WHITEBOARD_IMAGE_HANDLE_RADIUS + 6) {
        return { mode: "resize", payload: selectedPayload };
      }
    }

    for (const item of images) {
      const payload = item.payload;
      if (isPointInsideWhiteboardImage(point, payload)) {
        const imageEventId = Number(item.imageEventId || payload.image_event_id || 0);
        return {
          mode: imageEventId === selectedImageEventId ? "move" : "select",
          payload,
        };
      }
    }
    return null;
  }

  function buildWhiteboardImageDraft(basePayload, nextValues) {
    const nextWidth = Math.max(WHITEBOARD_IMAGE_MIN_RATIO, Math.min(1, Number(nextValues.width || basePayload.width || 0.2)));
    const nextHeight = Math.max(WHITEBOARD_IMAGE_MIN_RATIO, Math.min(1, Number(nextValues.height || basePayload.height || 0.2)));
    const nextX = Math.max(0, Math.min(1 - nextWidth, Number(nextValues.x ?? basePayload.x ?? 0)));
    const nextY = Math.max(0, Math.min(1 - nextHeight, Number(nextValues.y ?? basePayload.y ?? 0)));
    return normalizeWhiteboardImagePayload(
      {
        ...basePayload,
        ...nextValues,
        x: nextX,
        y: nextY,
        width: nextWidth,
        height: nextHeight,
        rotation_deg: normalizeRotationDegrees(nextValues.rotation_deg ?? basePayload.rotation_deg ?? 0),
      },
      basePayload.image_event_id
    );
  }

  async function saveWhiteboardImageTransform(imagePayload) {
    const state = ensureWhiteboardState();
    if (!imagePayload?.image_event_id || state.isUpdatingImage) {
      return;
    }
    state.isUpdatingImage = true;
    state.lastError = "";
    renderWhiteboardUi();
    try {
      const payload = await api(
        zbudujAdresZOrganizacja(`/api/whiteboard/images/${encodeURIComponent(imagePayload.image_event_id)}`),
        {
          method: "PATCH",
          body: JSON.stringify({
            x: imagePayload.x,
            y: imagePayload.y,
            width: imagePayload.width,
            height: imagePayload.height,
            rotation_deg: imagePayload.rotation_deg || 0,
          }),
        }
      );
      state.imageTransformDraft = null;
      state.selectedImageEventId = Number(imagePayload.image_event_id || 0);
      applyWhiteboardPayload(payload);
    } catch (error) {
      state.lastError = error.message;
      state.imageTransformDraft = null;
      renderWhiteboardCanvas();
      renderWhiteboardUi();
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie(error.message);
      }
    } finally {
      state.isUpdatingImage = false;
      renderWhiteboardUi();
    }
  }

  function calculateWhiteboardImagePlacement(file) {
    return new Promise((resolve, reject) => {
      const previewUrl = URL.createObjectURL(file);
      const image = new Image();
      image.onload = () => {
        const viewportWidth = Math.max(1, window.innerWidth || 1);
        const viewportHeight = Math.max(1, window.innerHeight || 1);
        const naturalWidth = Math.max(1, image.naturalWidth || 1);
        const naturalHeight = Math.max(1, image.naturalHeight || 1);
        const maxRenderedWidth = Math.min(viewportWidth * 0.44, 520);
        const maxRenderedHeight = Math.min(viewportHeight * 0.44, 380);
        const scale = Math.min(maxRenderedWidth / naturalWidth, maxRenderedHeight / naturalHeight, 1);
        const renderedWidth = naturalWidth * scale;
        const renderedHeight = naturalHeight * scale;
        const width = normalizeWhiteboardRatio(renderedWidth / viewportWidth, 0.08, 0.92);
        const height = normalizeWhiteboardRatio(renderedHeight / viewportHeight, 0.08, 0.92);
        resolve({
          width,
          height,
          x: normalizeWhiteboardRatio((1 - width) / 2, 0, Math.max(0, 1 - width)),
          y: normalizeWhiteboardRatio((1 - height) / 2, 0, Math.max(0, 1 - height)),
          rotation_deg: 0,
        });
        URL.revokeObjectURL(previewUrl);
      };
      image.onerror = () => {
        URL.revokeObjectURL(previewUrl);
        reject(new Error("Nie udalo sie odczytac obrazka."));
      };
      image.src = previewUrl;
    });
  }

  async function uploadWhiteboardImage(file) {
    const state = ensureWhiteboardState();
    const dom = getWhiteboardDom();
    if (!isWhiteboardVisible()) {
      return;
    }
    if (!file) {
      return;
    }

    state.toolbarOpen = true;
    state.isUploadingImage = true;
    state.lastError = "";
    renderWhiteboardUi();

    try {
      const placement = await calculateWhiteboardImagePlacement(file);
      const formData = new FormData();
      formData.append("file", file, file.name || "tablica.png");
      formData.append("x", String(placement.x));
      formData.append("y", String(placement.y));
      formData.append("width", String(placement.width));
      formData.append("height", String(placement.height));

      const payload = await api(zbudujAdresZOrganizacja("/api/whiteboard/images"), {
        method: "POST",
        body: formData,
      });
      const createdImage = Array.isArray(payload?.events)
        ? payload.events.find((event) => event?.event_type === "image")
        : null;
      if (createdImage?.whiteboard_event_id) {
        state.selectedImageEventId = Number(createdImage.whiteboard_event_id);
        state.imageEditEnabled = true;
        state.drawingEnabled = false;
      }
      applyWhiteboardPayload(payload);
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie("Dodano obrazek na wspolna tablice.");
      }
    } catch (error) {
      state.lastError = error.message;
      renderWhiteboardUi();
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie(error.message);
      }
    } finally {
      state.isUploadingImage = false;
      if (dom.imageInput) {
        dom.imageInput.value = "";
      }
      renderWhiteboardUi();
    }
  }

  function stopWhiteboardPolling() {
    const state = ensureWhiteboardState();
    if (state.pollTimeoutId) {
      window.clearTimeout(state.pollTimeoutId);
      state.pollTimeoutId = null;
    }
  }

  function scheduleWhiteboardPolling() {
    const state = ensureWhiteboardState();
    stopWhiteboardPolling();
    if (!canUseWhiteboard() || document.hidden) {
      return;
    }
    state.pollTimeoutId = window.setTimeout(async () => {
      await loadWhiteboardForCurrentScope(false);
      scheduleWhiteboardPolling();
    }, WHITEBOARD_POLL_INTERVAL_MS);
  }

  function discardLocalWhiteboardDraftsIfScopeChanged(nextOrganizationId) {
    const state = ensureWhiteboardState();
    if (
      state.scopeOrganizationId &&
      nextOrganizationId &&
      Number(state.scopeOrganizationId) !== Number(nextOrganizationId) &&
      (state.pendingStrokes.length > 0 || state.currentStroke)
    ) {
      state.pendingStrokes = [];
      state.currentStroke = null;
      state.lastError = "";
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie("Zmieniono organizacje. Niezapisane ruchy poprzedniej tablicy zostaly odrzucone.");
      }
    }
  }

  async function loadWhiteboardForCurrentScope(forceFull) {
    const state = ensureWhiteboardState();
    const nextOrganizationId = getWhiteboardScopeOrganizationId();

    if (!nextOrganizationId) {
      stopWhiteboardPolling();
      state.scopeOrganizationId = null;
      state.events = [];
      state.pendingStrokes = [];
      state.currentStroke = null;
      state.latestEventId = 0;
      state.lastClearedEventId = 0;
      state.isUploadingImage = false;
      state.isUpdatingImage = false;
      state.updatedAt = "";
      state.updatedBy = "";
      state.lastError = "";
      state.imageEditEnabled = false;
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
      clearWhiteboardImageCache();
      clearWhiteboardCanvas();
      renderWhiteboardUi();
      return;
    }

    discardLocalWhiteboardDraftsIfScopeChanged(nextOrganizationId);

    const scopeChanged = Number(state.scopeOrganizationId || 0) !== Number(nextOrganizationId || 0);
    if (scopeChanged) {
      state.scopeOrganizationId = nextOrganizationId;
      state.events = [];
      state.pendingStrokes = [];
      state.currentStroke = null;
      state.latestEventId = 0;
      state.lastClearedEventId = 0;
      clearWhiteboardImageCache();
      state.updatedAt = "";
      state.updatedBy = "";
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
      clearWhiteboardCanvas();
    }

    renderWhiteboardUi();

    const sinceEventId = !forceFull && !scopeChanged ? state.latestEventId : null;
    const whiteboardPath = sinceEventId
      ? `/api/whiteboard?since_event_id=${encodeURIComponent(sinceEventId)}`
      : "/api/whiteboard";

    try {
      const payload = await api(zbudujAdresZOrganizacja(whiteboardPath));
      state.scopeOrganizationId = nextOrganizationId;
      state.lastError = "";
      applyWhiteboardPayload(payload);
    } catch (error) {
      state.lastError = error.message;
      renderWhiteboardUi();
    }

    scheduleWhiteboardPolling();
  }

  async function clearWhiteboardRemotely() {
    const state = ensureWhiteboardState();
    if (!canUseWhiteboard()) {
      return;
    }
    if (!canClearWhiteboard()) {
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie("To konto nie moze wyczyscic tablicy organizacji.");
      }
      return;
    }
    if (!window.confirm("Czy na pewno wyczyscic wspolna tablice dla tej organizacji?")) {
      return;
    }

    state.pendingStrokes = [];
    state.currentStroke = null;
    renderWhiteboardCanvas();
    renderWhiteboardUi();

    try {
      const payload = await api(zbudujAdresZOrganizacja("/api/whiteboard/actions/clear"), {
        method: "POST",
      });
      applyWhiteboardPayload(payload);
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie("Wyczyszczono wspolna tablice organizacji.");
      }
    } catch (error) {
      state.lastError = error.message;
      renderWhiteboardUi();
      if (typeof pokazPowiadomienie === "function") {
        pokazPowiadomienie(error.message);
      }
    }
  }

  function beginWhiteboardImageInteraction(event) {
    const state = ensureWhiteboardState();
    if (!state.imageEditEnabled || !isWhiteboardVisible()) {
      return false;
    }
    if (event.pointerType === "mouse" && event.button !== 0) {
      return false;
    }
    const target = event.target instanceof Element ? event.target : null;
    if (getWhiteboardInteractiveTarget(target)) {
      return false;
    }

    const hit = findWhiteboardImageHit(getWhiteboardCanvasPoint(event));
    if (!hit) {
      if (state.selectedImageEventId) {
        state.selectedImageEventId = null;
        state.imageTransformDraft = null;
        state.imageInteraction = null;
        renderWhiteboardCanvas();
        renderWhiteboardUi();
      }
      event.preventDefault();
      return true;
    }

    state.selectedImageEventId = Number(hit.payload.image_event_id || 0);
    if (hit.mode === "select") {
      state.imageTransformDraft = null;
      state.imageInteraction = null;
      renderWhiteboardCanvas();
      renderWhiteboardUi();
      event.preventDefault();
      return true;
    }

    state.imageTransformDraft = normalizeWhiteboardImagePayload(hit.payload, hit.payload.image_event_id);
    state.imageInteraction = {
      pointerId: event.pointerId,
      mode: hit.mode,
      imageEventId: Number(hit.payload.image_event_id || 0),
      startNormalizedPoint: getNormalizedPointerPosition(event),
      startCanvasPoint: getWhiteboardCanvasPoint(event),
      initialPayload: normalizeWhiteboardImagePayload(hit.payload, hit.payload.image_event_id),
    };
    renderWhiteboardCanvas();
    renderWhiteboardUi();
    event.preventDefault();
    return true;
  }

  function continueWhiteboardImageInteraction(event) {
    const state = ensureWhiteboardState();
    const interaction = state.imageInteraction;
    if (!interaction || interaction.pointerId !== event.pointerId || !state.imageTransformDraft) {
      return false;
    }

    const initialPayload = interaction.initialPayload;
    const nextNormalizedPoint = getNormalizedPointerPosition(event);
    const nextCanvasPoint = getWhiteboardCanvasPoint(event);

    if (interaction.mode === "move") {
      state.imageTransformDraft = buildWhiteboardImageDraft(initialPayload, {
        x: Number(initialPayload.x || 0) + (nextNormalizedPoint.x - interaction.startNormalizedPoint.x),
        y: Number(initialPayload.y || 0) + (nextNormalizedPoint.y - interaction.startNormalizedPoint.y),
      });
    } else if (interaction.mode === "resize") {
      const center = getWhiteboardImageCenter(initialPayload);
      const localPoint = getWhiteboardImageLocalPoint(nextCanvasPoint, initialPayload);
      const { canvas } = getWhiteboardDom();
      const canvasWidth = Math.max(1, canvas?.clientWidth || window.innerWidth || 1);
      const canvasHeight = Math.max(1, canvas?.clientHeight || window.innerHeight || 1);
      const halfWidth = Math.max((WHITEBOARD_IMAGE_MIN_RATIO * canvasWidth) / 2, Math.abs(localPoint.x));
      const halfHeight = Math.max((WHITEBOARD_IMAGE_MIN_RATIO * canvasHeight) / 2, Math.abs(localPoint.y));
      state.imageTransformDraft = buildWhiteboardImageDraft(initialPayload, {
        width: (halfWidth * 2) / canvasWidth,
        height: (halfHeight * 2) / canvasHeight,
        x: (center.x - halfWidth) / canvasWidth,
        y: (center.y - halfHeight) / canvasHeight,
      });
    } else if (interaction.mode === "rotate") {
      const center = getWhiteboardImageCenter(initialPayload);
      const angle = Math.atan2(nextCanvasPoint.y - center.y, nextCanvasPoint.x - center.x);
      const startAngle = Math.atan2(
        interaction.startCanvasPoint.y - center.y,
        interaction.startCanvasPoint.x - center.x
      );
      state.imageTransformDraft = buildWhiteboardImageDraft(initialPayload, {
        rotation_deg:
          normalizeRotationDegrees(Number(initialPayload.rotation_deg || 0) + ((angle - startAngle) * 180) / Math.PI),
      });
    }

    renderWhiteboardCanvas();
    renderWhiteboardUi();
    event.preventDefault();
    return true;
  }

  function finishWhiteboardImageInteraction(event) {
    const state = ensureWhiteboardState();
    const interaction = state.imageInteraction;
    if (!interaction || interaction.pointerId !== event.pointerId) {
      return false;
    }
    const draft = state.imageTransformDraft
      ? normalizeWhiteboardImagePayload(state.imageTransformDraft, state.imageTransformDraft.image_event_id)
      : null;
    const initialPayload = interaction.initialPayload
      ? normalizeWhiteboardImagePayload(interaction.initialPayload, interaction.initialPayload.image_event_id)
      : null;
    state.imageInteraction = null;
    renderWhiteboardUi();
    if (
      draft &&
      initialPayload &&
      JSON.stringify({
        x: draft.x,
        y: draft.y,
        width: draft.width,
        height: draft.height,
        rotation_deg: draft.rotation_deg,
      }) !==
        JSON.stringify({
          x: initialPayload.x,
          y: initialPayload.y,
          width: initialPayload.width,
          height: initialPayload.height,
          rotation_deg: initialPayload.rotation_deg,
        })
    ) {
      void saveWhiteboardImageTransform(draft);
    } else {
      state.imageTransformDraft = null;
      renderWhiteboardCanvas();
    }
    event.preventDefault();
    return true;
  }

  function getNormalizedPointerPosition(event) {
    const { canvas } = getWhiteboardDom();
    if (!canvas) {
      return { x: 0, y: 0 };
    }
    const rect = canvas.getBoundingClientRect();
    const x = rect.width ? (event.clientX - rect.left) / rect.width : 0;
    const y = rect.height ? (event.clientY - rect.top) / rect.height : 0;
    return {
      x: Math.max(0, Math.min(1, Number(x.toFixed(6)))),
      y: Math.max(0, Math.min(1, Number(y.toFixed(6)))),
    };
  }

  function isFarEnoughFromLastPoint(points, nextPoint) {
    const lastPoint = points[points.length - 1];
    if (!lastPoint) {
      return true;
    }
    const deltaX = Number(nextPoint.x) - Number(lastPoint.x);
    const deltaY = Number(nextPoint.y) - Number(lastPoint.y);
    return Math.hypot(deltaX, deltaY) >= WHITEBOARD_POINT_DISTANCE_THRESHOLD;
  }

  function beginWhiteboardStroke(event) {
    const state = ensureWhiteboardState();
    if (!shouldHandleWhiteboardPointerEvent(event)) {
      return;
    }
    if (event.pointerType === "mouse" && event.button !== 0) {
      return;
    }

    const dom = getWhiteboardDom();
    const color = dom.colorInput?.value || "#0f5c90";
    const width = Number(dom.widthInput?.value || 4);
    state.currentStroke = {
      pointerId: event.pointerId,
      tool: state.eraserEnabled ? "eraser" : "pen",
      color,
      width,
      points: [getNormalizedPointerPosition(event)],
    };
    renderWhiteboardCanvas();
    event.preventDefault();
  }

  function continueWhiteboardStroke(event) {
    const state = ensureWhiteboardState();
    if (!state.currentStroke || state.currentStroke.pointerId !== event.pointerId) {
      return;
    }
    const nextPoint = getNormalizedPointerPosition(event);
    if (!isFarEnoughFromLastPoint(state.currentStroke.points, nextPoint)) {
      return;
    }
    state.currentStroke.points.push(nextPoint);
    renderWhiteboardCanvas();
    event.preventDefault();
  }

  function finishWhiteboardStroke(event) {
    const state = ensureWhiteboardState();
    if (!state.currentStroke || state.currentStroke.pointerId !== event.pointerId) {
      return;
    }
    const finalStroke = {
      tool: state.currentStroke.tool,
      color: state.currentStroke.color,
      width: Number(state.currentStroke.width || 4),
      points: Array.isArray(state.currentStroke.points) ? state.currentStroke.points.slice() : [],
    };
    state.currentStroke = null;
    if (finalStroke.points.length > 0) {
      queueWhiteboardStroke(finalStroke);
    } else {
      renderWhiteboardCanvas();
      renderWhiteboardUi();
    }
    event.preventDefault();
  }

  function bindWhiteboardDom() {
    const state = ensureWhiteboardState();
    const dom = getWhiteboardDom();
    if (state.domBound || !dom.canvas) {
      return;
    }
    state.domBound = true;

    dom.launcher?.addEventListener("click", () => {
      if (!stan.biezacyUzytkownik) {
        return;
      }
      if (!canUseWhiteboard()) {
        state.toolbarOpen = false;
        if (typeof pokazPowiadomienie === "function") {
          pokazPowiadomienie("Wybierz organizacje, aby uruchomic tablice.");
        }
        renderWhiteboardUi();
        return;
      }
      state.toolbarOpen = !state.toolbarOpen;
      renderWhiteboardUi();
    });
    dom.hideToolbarButton?.addEventListener("click", () => {
      state.toolbarOpen = false;
      state.drawingEnabled = false;
      state.imageEditEnabled = false;
      state.selectedImageEventId = null;
      state.imageTransformDraft = null;
      state.imageInteraction = null;
      renderWhiteboardUi();
    });
    dom.toggleBoardButton?.addEventListener("click", () => {
      if (!canUseWhiteboard()) {
        return;
      }
      state.toolbarOpen = true;
      state.boardVisible = !state.boardVisible;
      if (!state.boardVisible) {
        state.drawingEnabled = false;
        state.imageEditEnabled = false;
        state.interfaceHidden = false;
        state.selectedImageEventId = null;
        state.imageTransformDraft = null;
        state.imageInteraction = null;
      }
      renderWhiteboardUi();
    });
    dom.toggleDrawingButton?.addEventListener("click", () => {
      if (!isWhiteboardVisible()) {
        if (typeof pokazPowiadomienie === "function") {
          pokazPowiadomienie("Wlacz tablice, aby rozpoczac rysowanie.");
        }
        return;
      }
      state.toolbarOpen = true;
      state.drawingEnabled = !state.drawingEnabled;
      if (state.drawingEnabled) {
        state.imageEditEnabled = false;
        state.selectedImageEventId = null;
        state.imageTransformDraft = null;
        state.imageInteraction = null;
      }
      renderWhiteboardUi();
    });
    dom.toggleEraserButton?.addEventListener("click", () => {
      if (!isWhiteboardVisible()) {
        return;
      }
      state.toolbarOpen = true;
      state.eraserEnabled = !state.eraserEnabled;
      renderWhiteboardUi();
    });
    dom.toggleImageEditButton?.addEventListener("click", () => {
      if (!isWhiteboardVisible()) {
        if (typeof pokazPowiadomienie === "function") {
          pokazPowiadomienie("Wlacz tablice, aby edytowac obrazki.");
        }
        return;
      }
      state.toolbarOpen = true;
      state.imageEditEnabled = !state.imageEditEnabled;
      if (state.imageEditEnabled) {
        state.drawingEnabled = false;
        state.eraserEnabled = false;
      } else {
        state.selectedImageEventId = null;
        state.imageTransformDraft = null;
        state.imageInteraction = null;
      }
      renderWhiteboardCanvas();
      renderWhiteboardUi();
    });
    dom.toggleInterfaceButton?.addEventListener("click", () => {
      if (!isWhiteboardVisible()) {
        return;
      }
      state.toolbarOpen = true;
      state.interfaceHidden = !state.interfaceHidden;
      renderWhiteboardUi();
    });
    dom.addImageButton?.addEventListener("click", () => {
      if (!isWhiteboardVisible() || state.isUploadingImage) {
        return;
      }
      state.toolbarOpen = true;
      dom.imageInput?.click();
    });
    dom.imageInput?.addEventListener("change", () => {
      const file = dom.imageInput?.files?.[0];
      if (!file) {
        return;
      }
      void uploadWhiteboardImage(file);
    });
    dom.colorInput?.addEventListener("input", () => {
      state.toolbarOpen = true;
    });
    dom.widthInput?.addEventListener("input", () => {
      state.toolbarOpen = true;
      renderWhiteboardUi();
    });
    dom.saveNowButton?.addEventListener("click", async () => {
      await savePendingWhiteboardStrokes(true);
    });
    dom.clearButton?.addEventListener("click", async () => {
      await clearWhiteboardRemotely();
    });

    document.addEventListener(
      "pointerdown",
      (event) => {
        if (beginWhiteboardImageInteraction(event)) {
          return;
        }
        beginWhiteboardStroke(event);
      },
      true
    );
    document.addEventListener(
      "pointermove",
      (event) => {
        if (continueWhiteboardImageInteraction(event)) {
          return;
        }
        continueWhiteboardStroke(event);
      },
      { capture: true, passive: false }
    );
    document.addEventListener(
      "pointerup",
      (event) => {
        if (finishWhiteboardImageInteraction(event)) {
          return;
        }
        finishWhiteboardStroke(event);
      },
      true
    );
    document.addEventListener(
      "pointercancel",
      (event) => {
        if (finishWhiteboardImageInteraction(event)) {
          return;
        }
        finishWhiteboardStroke(event);
      },
      true
    );

    window.addEventListener("resize", resizeWhiteboardCanvas);
    document.addEventListener("visibilitychange", () => {
      if (document.hidden) {
        stopWhiteboardPolling();
        if (state.pendingStrokes.length > 0) {
          void savePendingWhiteboardStrokes(false);
        }
        return;
      }
      resizeWhiteboardCanvas();
      void loadWhiteboardForCurrentScope(false);
    });

    resizeWhiteboardCanvas();
    renderWhiteboardUi();
  }

  const originalOdswiezDanePoZalogowaniu = odswiezDanePoZalogowaniu;
  odswiezDanePoZalogowaniu = async function (...args) {
    const result = await originalOdswiezDanePoZalogowaniu.apply(this, args);
    await loadWhiteboardForCurrentScope(true);
    renderWhiteboardUi();
    return result;
  };

  const originalPrzygotujWidokPoWylogowaniu = przygotujWidokPoWylogowaniu;
  przygotujWidokPoWylogowaniu = function (...args) {
    stopWhiteboardPolling();
    const state = ensureWhiteboardState();
    state.events = [];
    state.pendingStrokes = [];
    state.currentStroke = null;
    state.scopeOrganizationId = null;
    state.latestEventId = 0;
    state.lastClearedEventId = 0;
    state.isSaving = false;
    state.isUploadingImage = false;
    state.isUpdatingImage = false;
    state.boardVisible = true;
    state.drawingEnabled = false;
    state.imageEditEnabled = false;
    state.eraserEnabled = false;
    state.interfaceHidden = false;
    state.toolbarOpen = false;
    state.lastError = "";
    state.updatedAt = "";
    state.updatedBy = "";
    state.selectedImageEventId = null;
    state.imageTransformDraft = null;
    state.imageInteraction = null;
    clearWhiteboardImageCache();
    clearWhiteboardCanvas();
    const result = originalPrzygotujWidokPoWylogowaniu.apply(this, args);
    renderWhiteboardUi();
    return result;
  };

  const originalOdswiezPasekSesji = odswiezPasekSesji;
  odswiezPasekSesji = function (...args) {
    const result = originalOdswiezPasekSesji.apply(this, args);
    renderWhiteboardUi();
    return result;
  };

  bindWhiteboardDom();
  renderWhiteboardUi();
})();
