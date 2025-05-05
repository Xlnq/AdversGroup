class GraphicEditor {

    constructor(config) {
        this.config = config;
        this.preview3D = new Preview3D();
        this.state = {
            currentSide: 'front',
            selectedElement: null,
            selectedGroup: null,
            elements: [],
            groups: {},
            nextZIndex: 1,
            printingMethod: 'silk',
            printingSide: 'front',
            canvasConstraints: config.printingMethods.silk,
            history: [],
            historyIndex: -1
        };


        this.config.printingMethods = {
            silk: {
                width: 23,  // cm
                height: 30,
                unit: 'cm',
                printableArea: { x: 0, y: 0, width: 23, height: 30 }
            },
            embroidery: {
                diameter: 17,
                unit: 'cm',
                printableArea: { x: 0, y: 0, width: 17, height: 17 }
            },
            transfer: {
                width: 24,
                height: 35,
                unit: 'cm',
                printableArea: { x: 0, y: 0, width: 24, height: 35 }
            }
        };

        this.dom = {};
        this.init();
    }

    init() {
        this.cacheDOM();
        this.initCanvas();
        this.setupEventListeners();
        this.loadInitialElements();
        this.updateUI();
    }

    cacheDOM() {
        this.dom.editorContainer = document.querySelector('.editor-container');
        if (!this.dom.editorContainer) {
            console.error('Основной контейнер редактора не найден');
            return;
        }

        this.dom.previewBtn = document.getElementById('preview-btn');
        this.dom.generatePdfBtn = document.getElementById('generate-pdf');

        if (!this.dom.previewBtn || !this.dom.generatePdfBtn) {
            console.error('Кнопки действий не найдены:', {
                previewBtn: this.dom.previewBtn,
                generatePdfBtn: this.dom.generatePdfBtn
            });
        }

        this.dom.frontCanvas = document.getElementById('front-editable-canvas');
        this.dom.backCanvas = document.getElementById('back-editable-canvas');
        if (!this.dom.frontCanvas || !this.dom.backCanvas) {
            console.error('Холсты не найдены:', {
                frontCanvas: this.dom.frontCanvas,
                backCanvas: this.dom.backCanvas
            });
        }

        this.dom.frontCanvasArea = document.getElementById('front-canvas-area');
        this.dom.backCanvasArea = document.getElementById('back-canvas-area');

        this.dom.methodSelect = document.getElementById('printing-method');
        this.dom.sideSelect = document.getElementById('printing-side');
        this.dom.designName = document.getElementById('design-name');

        this.dom.addTextBtn = document.getElementById('add-text');
        this.dom.addImageBtn = document.getElementById('add-image');
        this.dom.imageUpload = document.getElementById('image-upload');
        this.dom.textOptions = document.querySelector('.text-options');
        this.dom.textContent = document.getElementById('text-content');
        this.dom.textColor = document.getElementById('text-color');
        this.dom.textFont = document.getElementById('text-font');
        this.dom.textSize = document.getElementById('text-size');
        this.dom.applyTextBtn = document.getElementById('apply-text');

        this.dom.propertiesPanel = document.querySelector('.properties-panel');
        this.dom.propX = document.getElementById('prop-x');
        this.dom.propY = document.getElementById('prop-y');
        this.dom.propWidth = document.getElementById('prop-width');
        this.dom.propHeight = document.getElementById('prop-height');
        this.dom.propRotation = document.getElementById('prop-rotation');
        this.dom.propOpacity = document.getElementById('prop-opacity');
        this.dom.updatePropsBtn = document.getElementById('update-properties');
        this.dom.deleteElementBtn = document.getElementById('delete-element');

        this.dom.saveDesignBtn = document.getElementById('save-design');

        this.dom.undoBtn = document.getElementById('undo-btn');
        this.dom.redoBtn = document.getElementById('redo-btn');

        this.dom.alignLeftBtn = document.getElementById('align-left');
        this.dom.alignCenterBtn = document.getElementById('align-center');
        this.dom.alignRightBtn = document.getElementById('align-right');
        this.dom.alignTopBtn = document.getElementById('align-top');
        this.dom.alignMiddleBtn = document.getElementById('align-middle');
        this.dom.alignBottomBtn = document.getElementById('align-bottom');

        this.dom.groupBtn = document.getElementById('group-btn');
        this.dom.ungroupBtn = document.getElementById('ungroup-btn');

        this.dom.layerUpBtn = document.getElementById('layer-up');
        this.dom.layerDownBtn = document.getElementById('layer-down');
        this.dom.layersPanel = document.getElementById('layers-panel');
    }

    initCanvas() {
        this.updateCanvasSize(this.dom.methodSelect.value);
    }

    switchSide(side) {
        this.state.currentSide = side;
        document.querySelectorAll('.canvas-wrapper').forEach(wrapper => {
            wrapper.classList.remove('active');
        });
        document.getElementById(`${side}-canvas`).classList.add('active');

        document.querySelectorAll('.btn-side').forEach(btn => {
            btn.classList.remove('active');
        });
        document.getElementById(`${side}-side`).classList.add('active');
    }

    applyElementProperties(elementState) {
        const { element, data } = elementState;

        element.style.left = `${data.x}px`;
        element.style.top = `${data.y}px`;
        element.style.transform = `rotate(${data.rotation}deg)`;
        element.style.opacity = data.opacity;
        element.style.zIndex = data.zIndex;

        if (data.type === 'image') {
            element.style.width = `${data.width}px`;
            element.style.height = `${data.height}px`;
        }
    }

    setupEventListeners() {
        document.getElementById('front-side').addEventListener('click', () => this.switchSide('front'));
        document.getElementById('back-side').addEventListener('click', () => this.switchSide('back'));

        this.dom.methodSelect.addEventListener('change', (e) => {
            this.state.printingMethod = e.target.value;
            this.state.canvasConstraints = this.config.printingMethods[e.target.value];
            this.updateCanvasSize(e.target.value);
        });

        this.dom.sideSelect.addEventListener('change', (e) => {
            this.state.printingSide = e.target.value;
            this.toggleCanvasSide(e.target.value);

            if (e.target.value !== 'both') {
                this.switchSide(e.target.value);
            }
        });

        this.dom.addTextBtn.addEventListener('click', () => this.showTextInput());
        this.dom.addImageBtn.addEventListener('click', () => this.dom.imageUpload.click());
        this.dom.imageUpload.addEventListener('change', (e) => this.handleImageUpload(e));
        this.dom.applyTextBtn.addEventListener('click', () => this.createTextElement());

        [this.dom.frontCanvas, this.dom.backCanvas].forEach(canvas => {
            canvas.addEventListener('mousedown', (e) => this.handleCanvasClick(e));
        });

        this.dom.updatePropsBtn.addEventListener('click', () => {
            if (!this.state.selectedElement) return;

            const element = this.state.selectedElement;

            element.data.x = parseInt(this.dom.propX.value) || 0;
            element.data.y = parseInt(this.dom.propY.value) || 0;
            element.data.rotation = parseInt(this.dom.propRotation.value) || 0;
            element.data.opacity = parseFloat(this.dom.propOpacity.value) || 1;

            if (element.data.type === 'image') {
                element.data.width = parseInt(this.dom.propWidth.value) || 0;
                element.data.height = parseInt(this.dom.propHeight.value) || 0;
            }

            this.applyElementProperties(element);
            this.saveState();
        });

        this.dom.deleteElementBtn.addEventListener('click', () => this.deleteSelectedElement());
        document.querySelector('.btn-close-panel').addEventListener('click', () => {
            this.dom.propertiesPanel.style.display = 'none';
            if (this.state.selectedElement) {
                this.state.selectedElement.element.classList.remove('selected');
                this.state.selectedElement = null;
            }
        });

        this.dom.saveDesignBtn.addEventListener('click', () => this.saveDesign());
        this.dom.generatePdfBtn.addEventListener('click', () => this.generatePdf());

        this.dom.undoBtn.addEventListener('click', () => this.undo());
        this.dom.redoBtn.addEventListener('click', () => this.redo());

        const previewBtn = document.getElementById('preview-3d');
        if (previewBtn) {
            previewBtn.addEventListener('click', (e) => {
                e.preventDefault();
                this.preview3D.show3dPreview();
            });
        } else {
            console.error('Preview 3D button not found');
        }

        this.dom.alignLeftBtn.addEventListener('click', () => this.alignElements('left'));
        this.dom.alignCenterBtn.addEventListener('click', () => this.alignElements('center'));
        this.dom.alignRightBtn.addEventListener('click', () => this.alignElements('right'));
        this.dom.alignTopBtn.addEventListener('click', () => this.alignElements('top'));
        this.dom.alignMiddleBtn.addEventListener('click', () => this.alignElements('middle'));
        this.dom.alignBottomBtn.addEventListener('click', () => this.alignElements('bottom'));

        this.dom.groupBtn.addEventListener('click', () => this.groupElements());
        this.dom.ungroupBtn.addEventListener('click', () => this.ungroupElements());

        this.dom.layerUpBtn.addEventListener('click', () => this.moveLayer(1));
        this.dom.layerDownBtn.addEventListener('click', () => this.moveLayer(-1));

        document.addEventListener('keydown', (e) => this.handleKeyboardShortcuts(e));
    }

    updateCanvasSize(method) {
        const constraints = this.config.printingMethods[method];
        if (!constraints) return;

        [this.dom.frontCanvasArea, this.dom.backCanvasArea].forEach(area => {
            if (method === 'embroidery') {
                area.style.width = `${constraints.diameter}${constraints.unit}`;
                area.style.height = `${constraints.diameter}${constraints.unit}`;
                area.style.borderRadius = '50%';
            } else {
                area.style.width = `${constraints.width}${constraints.unit}`;
                area.style.height = `${constraints.height}${constraints.unit}`;
                area.style.borderRadius = '0';
            }
        });
    }

    toggleCanvasSide(side) {
        const frontWrapper = document.getElementById('front-canvas');
        const backWrapper = document.getElementById('back-canvas');

        switch(side) {
            case 'front':
                frontWrapper.classList.add('active');
                backWrapper.classList.remove('active');
                break;
            case 'back':
                frontWrapper.classList.remove('active');
                backWrapper.classList.add('active');
                break;
            case 'both':
                frontWrapper.classList.add('active');
                backWrapper.classList.add('active');
                break;
        }
    }

    showTextInput() {
        this.dom.textOptions.style.display = 'block';
        this.dom.textContent.focus();
    }

    createTextElement() {
        const text = this.dom.textContent.value.trim();
        if (!text) return;

        const elementData = {
            id: `element-${Date.now()}`,
            type: 'text',
            side: this.state.currentSide,
            content: text,
            x: 100,
            y: 100,
            color: this.dom.textColor.value,
            fontFamily: this.dom.textFont.value,
            fontSize: parseInt(this.dom.textSize.value),
            rotation: 0,
            zIndex: this.state.nextZIndex++,
            opacity: 1
        };

        this.addElementToCanvas(elementData);

        this.dom.textContent.value = '';
        this.dom.textOptions.style.display = 'none';
    }

    addElementToCanvas(elementData) {
        const element = document.createElement('div');
        element.className = 'canvas-element';
        element.dataset.id = elementData.id;
        element.dataset.type = elementData.type;
        element.dataset.side = elementData.side;

        element.style.position = 'absolute';
        element.style.left = `${elementData.x}px`;
        element.style.top = `${elementData.y}px`;
        element.style.zIndex = elementData.zIndex;

        if (elementData.type === 'text') {
            element.innerHTML = `
                <span style="color:${elementData.color};
                            font-family:${elementData.fontFamily};
                            font-size:${elementData.fontSize}px">
                    ${elementData.content}
                </span>
            `;
        } else if (elementData.type === 'image') {
            const img = document.createElement('img');
            img.src = elementData.content;
            img.style.maxWidth = '100%';
            img.style.maxHeight = '100%';
            element.appendChild(img);

            if (elementData.width) element.style.width = `${elementData.width}px`;
            if (elementData.height) element.style.height = `${elementData.height}px`;
        }

        this.dom[`${elementData.side}Canvas`].appendChild(element);

        const elementState = {
            id: elementData.id,
            element: element,
            data: elementData
        };

        this.state.elements.push(elementState);
        this.setupElementInteractions(elementState);
        this.saveState();
        this.updateUI();
    }

    handleImageUpload(event) {
        const file = event.target.files[0];
        if (!file) return;

        const reader = new FileReader();
        reader.onload = (e) => {
            const img = new Image();
            img.onload = () => {
                const elementData = {
                    id: `element-${Date.now()}`,
                    type: 'image',
                    side: this.state.currentSide,
                    content: e.target.result,
                    x: 100,
                    y: 100,
                    width: img.width,
                    height: img.height,
                    rotation: 0,
                    zIndex: this.state.nextZIndex++,
                    opacity: 1,
                    naturalWidth: img.width,
                    naturalHeight: img.height
                };

                this.addElementToCanvas(elementData);
            };
            img.src = e.target.result;
        };
        reader.readAsDataURL(file);
        event.target.value = '';
    }

    setupElementInteractions(elementState) {
        const { element } = elementState;
        let isDragging = false;
        let isResizing = false;
        let startX, startY, initialX, initialY, initialWidth, initialHeight;

        // Создаем маркер для изменения размера только для изображений
        if (elementState.data.type === 'image') {
            const resizeHandle = document.createElement('div');
            resizeHandle.className = 'resize-handle';
            element.appendChild(resizeHandle);

            // Обработчик для изменения размера
            resizeHandle.addEventListener('mousedown', (e) => {
                e.stopPropagation();
                e.preventDefault();

                isResizing = true;
                startX = e.clientX;
                startY = e.clientY;
                initialWidth = elementState.data.width;
                initialHeight = elementState.data.height;

                // Блокируем события перемещения
                element.style.pointerEvents = 'none';

                document.addEventListener('mousemove', handleResize);
                document.addEventListener('mouseup', stopResize, { once: true });
            });
        }

        // Обработчик для перемещения
        element.addEventListener('mousedown', (e) => {
            // Игнорируем клики на resize handle
            if (e.target.classList.contains('resize-handle')) {
                return;
            }

            e.stopPropagation();
            e.preventDefault();

            this.clearSelection();
            element.classList.add('selected');
            this.state.selectedElement = elementState;
            this.updatePropertiesPanel();

            if (e.button === 0) {
                isDragging = true;
                startX = e.clientX;
                startY = e.clientY;

                initialX = elementState.data.x;
                initialY = elementState.data.y;

                document.addEventListener('mousemove', drag);
                document.addEventListener('mouseup', stopDrag, { once: true });
            }
        });

        const drag = (e) => {
            if (!isDragging || isResizing) return;

            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            const newX = initialX + dx;
            const newY = initialY + dy;

            const canvas = this.dom[`${elementState.data.side}Canvas`];
            const maxX = canvas.clientWidth - element.offsetWidth;
            const maxY = canvas.clientHeight - element.offsetHeight;

            const boundedX = Math.max(0, Math.min(maxX, newX));
            const boundedY = Math.max(0, Math.min(maxY, newY));

            element.style.left = `${boundedX}px`;
            element.style.top = `${boundedY}px`;

            elementState.data.x = boundedX;
            elementState.data.y = boundedY;

            this.updatePropertiesPanel();
        };

        const stopDrag = () => {
            isDragging = false;
            document.removeEventListener('mousemove', drag);
            this.saveState();
        };

        const handleResize = (e) => {
            if (!isResizing) return;

            const dx = e.clientX - startX;
            const dy = e.clientY - startY;

            let newWidth = Math.max(10, initialWidth + dx);
            let newHeight = Math.max(10, initialHeight + dy);

            // Сохраняем пропорции при зажатом Shift
            if (e.shiftKey && elementState.data.naturalWidth && elementState.data.naturalHeight) {
                const aspectRatio = elementState.data.naturalWidth / elementState.data.naturalHeight;
                newHeight = newWidth / aspectRatio;
            }

            element.style.width = `${newWidth}px`;
            element.style.height = `${newHeight}px`;
            elementState.data.width = newWidth;
            elementState.data.height = newHeight;

            this.updatePropertiesPanel();
        };

        const stopResize = () => {
            isResizing = false;
            document.removeEventListener('mousemove', handleResize);
            element.style.pointerEvents = 'auto';
            this.saveState();
        };

        if (element.dataset.type === 'text') {
            element.addEventListener('dblclick', (e) => {
                e.stopPropagation();
                const newText = prompt('Редактировать текст:', elementState.data.content);
                if (newText !== null) {
                    elementState.data.content = newText;
                    element.querySelector('span').textContent = newText;
                    this.saveState();
                }
            });
        }
    }

    clearSelection() {
        if (this.state.selectedElement) {
            this.state.selectedElement.element.classList.remove('selected');
        }
        this.state.selectedElement = null;
        this.state.selectedGroup = null;
    }

    showPropertiesPanel(elementState) {
        if (!elementState) return;

        this.dom.propertiesPanel.style.display = 'block';
        this.dom.propsTitle.textContent = elementState.data.type === 'text' ? 'Текст' : 'Изображение';

        const { data } = elementState;
        this.dom.propX.value = data.x;
        this.dom.propY.value = data.y;
        this.dom.propRotation.value = data.rotation || 0;
        this.dom.propOpacity.value = data.opacity || 1;

        if (data.width) this.dom.propWidth.value = data.width;
        if (data.height) this.dom.propHeight.value = data.height;
    }

    deleteSelectedElement() {
        if (!this.state.selectedElement) return;

        const index = this.state.elements.findIndex(el => el.id === this.state.selectedElement.id);
        if (index !== -1) {
            this.state.elements[index].element.remove();
            this.state.elements.splice(index, 1);
        }

        this.clearSelection();
        this.dom.propertiesPanel.style.display = 'none';
        this.saveState();
        this.updateUI();
    }

    saveState() {
        if (this.state.historyIndex < this.state.history.length - 1) {
            this.state.history = this.state.history.slice(0, this.state.historyIndex + 1);
        }

        const stateCopy = {
            elements: this.state.elements.map(el => ({ ...el.data })),
            nextZIndex: this.state.nextZIndex,
            groups: JSON.parse(JSON.stringify(this.state.groups))
        };

        this.state.history.push(stateCopy);
        this.state.historyIndex = this.state.history.length - 1;

        if (this.state.history.length > this.config.maxHistorySteps) {
            this.state.history.shift();
            this.state.historyIndex--;
        }

        this.updateUndoRedoButtons();
    }

    undo() {
        if (this.state.historyIndex <= 0) return;

        this.state.historyIndex--;
        this.restoreFromHistory();
    }

    redo() {
        if (this.state.historyIndex >= this.state.history.length - 1) return;

        this.state.historyIndex++;
        this.restoreFromHistory();
    }

    restoreFromHistory() {
        const historyState = this.state.history[this.state.historyIndex];

        this.clearCanvas();

        historyState.elements.forEach(elementData => {
            this.addElementToCanvas(elementData);
        });

        this.state.nextZIndex = historyState.nextZIndex;
        this.state.groups = JSON.parse(JSON.stringify(historyState.groups));

        this.updateUI();
    }

    updateUndoRedoButtons() {
        this.dom.undoBtn.disabled = this.state.historyIndex <= 0;
        this.dom.redoBtn.disabled = this.state.historyIndex >= this.state.history.length - 1;
    }

    alignElements(alignment) {
        if (!this.state.selectedElement) return;

        const canvas = this.state.currentSide === 'front' ?
            this.dom.frontCanvasArea : this.dom.backCanvasArea;
        const canvasRect = canvas.getBoundingClientRect();

        const element = this.state.selectedElement.element;
        const elementRect = element.getBoundingClientRect();

        let newX = this.state.selectedElement.data.x;
        let newY = this.state.selectedElement.data.y;

        switch(alignment) {
            case 'left':
                newX = 0;
                break;
            case 'center':
                newX = (canvasRect.width - elementRect.width) / 2;
                break;
            case 'right':
                newX = canvasRect.width - elementRect.width;
                break;
            case 'top':
                newY = 0;
                break;
            case 'middle':
                newY = (canvasRect.height - elementRect.height) / 2;
                break;
            case 'bottom':
                newY = canvasRect.height - elementRect.height;
                break;
        }

        element.style.left = `${newX}px`;
        element.style.top = `${newY}px`;
        this.state.selectedElement.data.x = newX;
        this.state.selectedElement.data.y = newY;

        this.saveState();
        this.updatePropertiesPanel();
    }

    groupElements() {
        if (!this.state.selectedElement ||
            this.state.elements.filter(el => el.element.classList.contains('selected')).length < 2) {
            alert('Выберите минимум 2 элемента для группировки');
            return;
        }

        const selectedElements = this.state.elements.filter(el => el.element.classList.contains('selected'));
        const groupId = `group-${Date.now()}`;

        this.state.groups[groupId] = selectedElements.map(el => el.id);

        selectedElements.forEach(el => {
            el.element.classList.add('grouped');
            el.element.dataset.group = groupId;
        });

        this.state.selectedGroup = groupId;
        this.state.selectedElement = null;

        this.saveState();
        this.updatePropertiesPanel();
    }

    ungroupElements() {
        if (!this.state.selectedGroup) return;

        const groupElements = this.state.groups[this.state.selectedGroup];
        if (!groupElements) return;

        groupElements.forEach(id => {
            const el = this.state.elements.find(el => el.id === id);
            if (el) {
                el.element.classList.remove('grouped');
                delete el.element.dataset.group;
            }
        });

        delete this.state.groups[this.state.selectedGroup];
        this.state.selectedGroup = null;

        this.saveState();
        this.updatePropertiesPanel();
    }

    moveLayer(direction) {
        if (!this.state.selectedElement) return;

        const currentElement = this.state.selectedElement;
        const currentZIndex = currentElement.data.zIndex;

        let targetElement = null;
        let minDiff = Infinity;

        this.state.elements.forEach(el => {
            if (el.id === currentElement.id) return;

            const diff = el.data.zIndex - currentZIndex;

            if (direction > 0 && diff > 0 && diff < minDiff) {
                minDiff = diff;
                targetElement = el;
            } else if (direction < 0 && diff < 0 && Math.abs(diff) < minDiff) {
                minDiff = Math.abs(diff);
                targetElement = el;
            }
        });

        if (targetElement) {
            const tempZIndex = currentElement.data.zIndex;
            currentElement.data.zIndex = targetElement.data.zIndex;
            targetElement.data.zIndex = tempZIndex;

            currentElement.element.style.zIndex = currentElement.data.zIndex;
            targetElement.element.style.zIndex = targetElement.data.zIndex;

            this.saveState();
            this.updateLayersPanel();
        }
    }

    updateLayersPanel() {
        this.dom.layersPanel.innerHTML = '';

        const sortedElements = [...this.state.elements].sort((a, b) => b.data.zIndex - a.data.zIndex);

        sortedElements.forEach(el => {
            const layerItem = document.createElement('div');
            layerItem.className = 'layer-item';
            if (this.state.selectedElement && this.state.selectedElement.id === el.id) {
                layerItem.classList.add('selected');
            }

            layerItem.innerHTML = `
                <span class="layer-icon">${el.data.type === 'text' ? 'T' : '🖼️'}</span>
                <span class="layer-name">${el.data.type === 'text' ? 
                    (el.data.content.length > 15 ? el.data.content.substring(0, 15) + '...' : el.data.content) : 
                    'Изображение'}</span>
                <span class="layer-zindex">${el.data.zIndex}</span>
            `;

            layerItem.addEventListener('click', () => {
                this.clearSelection();
                el.element.classList.add('selected');
                this.state.selectedElement = el;
                this.showPropertiesPanel(el);
            });

            this.dom.layersPanel.appendChild(layerItem);
        });
    }

    saveDesign() {
        if (!this.dom.designName) {
            console.error('Element designName not found');
            return;
        }

        const designName = this.dom.designName.value.trim();
        if (!designName) {
            alert('Пожалуйста, введите название дизайна');
            return;
        }

        console.log('Saving design with elements:', this.state.elements);

        const elementsToSave = this.state.elements.map(el => {
            if (!el || !el.data) {
                console.error('Invalid element structure:', el);
                return null;
            }

            const elementData = {
                id: el.id,
                type: el.data.type,
                side: el.data.side,
                content: el.data.content,
                x: el.data.x,
                y: el.data.y,
                rotation: el.data.rotation,
                zIndex: el.data.zIndex,
                opacity: el.data.opacity
            };

            if (el.data.width) elementData.width = el.data.width;
            if (el.data.height) elementData.height = el.data.height;
            if (el.data.color) elementData.color = el.data.color;
            if (el.data.fontFamily) elementData.fontFamily = el.data.fontFamily;
            if (el.data.fontSize) elementData.fontSize = el.data.fontSize;

            return elementData;
        }).filter(el => el !== null);

        const csrfToken = this.getCookie('csrftoken');
        if (!csrfToken) {
            alert('Ошибка безопасности. Пожалуйста, перезагрузите страницу.');
            return;
        }

        console.log('Sending data to server:', {
            design_id: this.config.designId || '',
            product_id: this.config.productId,
            name: designName,
            printing_method: this.state.printingMethod,
            printing_side: this.state.printingSide,
            elements: elementsToSave
        });

        fetch(`/products/${this.config.productId}/design/save/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': csrfToken,
            },
            body: JSON.stringify({
                design_id: this.config.designId || '',
                product_id: this.config.productId,
                name: designName,
                printing_method: this.state.printingMethod,
                printing_side: this.state.printingSide,
                elements: elementsToSave,
                clear_existing: true
            })
        })
        .then(response => {
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            console.log('Server response:', data);
            if (data.status === 'success') {
                if (!this.config.designId) {
                    this.config.designId = data.design_id;
                    history.pushState(null, '', `/products/${this.config.productId}/design/${this.config.designId}/`);
                }
                this.updateActionButtons();
                alert('Дизайн успешно сохранен!');
            } else {
                throw new Error(data.message || 'Ошибка при сохранении дизайна');
            }
        })
        .catch(error => {
            console.error('Ошибка сохранения:', error);
            alert('Ошибка сохранения: ' + error.message);
        });
    }

    generatePdf() {
        if (!this.config.designId) {
            alert('Пожалуйста, сначала сохраните дизайн');
            return;
        }

        const method = this.state.printingMethod;
        const constraints = this.config.printingMethods[method];
        let pageWidth, pageHeight;

        if (method === 'embroidery') {
            pageWidth = constraints.diameter;
            pageHeight = constraints.diameter;
        } else {
            pageWidth = constraints.width;
            pageHeight = constraints.height;
        }

        const widthPt = pageWidth * 28.35;
        const heightPt = pageHeight * 28.35;

        const designData = {
            front: this.getCanvasData('front'),
            back: this.getCanvasData('back'),
            printingMethod: method,
            designId: this.config.designId,
            pageSize: { width: widthPt, height: heightPt }
        };

        fetch(`/products/${this.config.productId}/design/${this.config.designId}/generate-pdf/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': this.getCookie('csrftoken'),
            },
            body: JSON.stringify(designData)
        })
        .then(response => response.blob())
        .then(blob => {
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement('a');
            a.href = url;
            a.download = `design-${this.config.designId}.pdf`;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
            document.body.removeChild(a);
        })
        .catch(error => {
            console.error('Error:', error);
            alert('Ошибка при генерации PDF: ' + error.message);
        });
    }

    getCanvasData(side) {
        const canvas = this.dom[`${side}Canvas`];
        const elements = this.state.elements
            .filter(el => el.data.side === side)
            .map(el => {
                const elementData = {
                    type: el.data.type,
                    content: el.data.content,
                    x: el.data.x,
                    y: el.data.y,
                    width: el.data.width,
                    height: el.data.height,
                    rotation: el.data.rotation,
                    color: el.data.color,
                    fontFamily: el.data.fontFamily,
                    fontSize: el.data.fontSize,
                    zIndex: el.data.zIndex,
                    opacity: el.data.opacity
                };

                if (el.data.type === 'image' && el.data.content.startsWith('data:')) {
                    elementData.content = el.data.content;
                }

                return elementData;
            });

        return {
            width: canvas.clientWidth,
            height: canvas.clientHeight,
            elements: elements
        };
    }

    updateActionButtons() {
        if (!this.dom.previewBtn || !this.dom.generatePdfBtn) {
            console.error('Action buttons not initialized');
            return;
        }

        if (this.config.designId) {
            this.safeAddClass(this.dom.previewBtn, 'disabled', false);
            this.safeAddClass(this.dom.generatePdfBtn, 'disabled', false);
        } else {
            this.safeAddClass(this.dom.previewBtn, 'disabled', true);
            this.safeAddClass(this.dom.generatePdfBtn, 'disabled', true);
        }
    }

    safeAddClass(element, className, shouldAdd = true) {
        if (!element || !element.classList) {
            console.error(`Cannot ${shouldAdd ? 'add' : 'remove'} class to null element`);
            return;
        }

        if (shouldAdd) {
            element.classList.add(className);
        } else {
            element.classList.remove(className);
        }
    }

    getCookie(name) {
        let cookieValue = null;
        if (document.cookie && document.cookie !== '') {
            const cookies = document.cookie.split(';');
            for (let i = 0; i < cookies.length; i++) {
                const cookie = cookies[i].trim();
                if (cookie.substring(0, name.length + 1) === (name + '=')) {
                    cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                    break;
                }
            }
        }
        return cookieValue;
    }

    handleKeyboardShortcuts(e) {
        if (e.ctrlKey && e.key === 'z') {
            e.preventDefault();
            this.undo();
        }

        if (e.ctrlKey && e.shiftKey && e.key === 'Z') {
            e.preventDefault();
            this.redo();
        }

        if (e.key === 'Delete') {
            e.preventDefault();
            this.deleteSelectedElement();
        }
    }

    loadInitialElements() {
        if (this.config.initialElements?.length > 0) {
            this.config.initialElements.forEach(element => {
                this.addElementToCanvas(element);
                if (element.zIndex >= this.state.nextZIndex) {
                    this.state.nextZIndex = element.zIndex + 1;
                }
            });
        }
    }


    updateUI() {
        this.updateElementCounter();
        this.updateLayersPanel();
        this.updateUndoRedoButtons();
        this.updateActionButtons();
    }

    updateElementCounter() {
        const count = this.state.elements.length;
        const counter = document.getElementById('element-counter');
        if (counter) {
            counter.textContent = `${count}/${this.config.maxElements}`;
            counter.className = count >= this.config.maxElements ?
                'element-counter limit-reached' : 'element-counter';
        }
    }

    handleCanvasClick(e) {
        if (e.target === this.dom.frontCanvas || e.target === this.dom.backCanvas) {
            this.clearSelection();
            this.dom.propertiesPanel.style.display = 'none';
        }
    }

    updatePropertiesPanel() {
        if (!this.state.selectedElement) {
            this.dom.propertiesPanel.style.display = 'none';
            return;
        }

        const element = this.state.selectedElement;
        this.dom.propertiesPanel.style.display = 'block';

        document.getElementById('props-title').textContent =
            element.data.type === 'text' ? 'Текст' : 'Изображение';

        this.dom.propX.value = element.data.x;
        this.dom.propY.value = element.data.y;
        this.dom.propRotation.value = element.data.rotation || 0;
        this.dom.propOpacity.value = element.data.opacity || 1;

        const widthHeightGroups = [
            this.dom.propWidth.closest('.form-group'),
            this.dom.propHeight.closest('.form-group')
        ];

        if (element.data.type === 'image') {
            this.dom.propWidth.value = element.data.width || '';
            this.dom.propHeight.value = element.data.height || '';
            widthHeightGroups.forEach(group => group.style.display = 'block');
        } else {
            widthHeightGroups.forEach(group => group.style.display = 'none');
        }
    }

}

class Preview3D {
    constructor(config = {}) {
        this.config = config;
        this.modelPath = config.modelPath || '/static/models/Last.glb';
        this.container = null;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.controls = null;
        this.animationId = null;
        this.model = null;
    }

    async show3dPreview() {
        try {
            this.createContainer();

            this.initThreeJS();

            this.setupLighting();

            await this.loadModel();

            await this.applyDesignToModel();

            this.setupEventListeners();

            this.startAnimation();
        } catch (error) {
            console.error('Error initializing 3D preview:', error);
            this.showError();
        }
    }

    createContainer() {
        this.container = document.createElement('div');
        this.container.id = 'preview-3d-container';
        Object.assign(this.container.style, {
            position: 'fixed',
            top: '0',
            left: '0',
            width: '100%',
            height: '100%',
            backgroundColor: 'rgba(0,0,0,0.8)',
            zIndex: '10000',
            display: 'flex',
            justifyContent: 'center',
            alignItems: 'center'
        });

        const closeBtn = document.createElement('button');
        Object.assign(closeBtn.style, {
            position: 'absolute',
            top: '20px',
            right: '20px',
            fontSize: '24px',
            background: 'transparent',
            border: 'none',
            color: 'white',
            cursor: 'pointer',
            zIndex: '10001'
        });
        closeBtn.textContent = '×';
        closeBtn.onclick = () => this.closePreview();

        this.container.appendChild(closeBtn);
        document.body.appendChild(this.container);
    }

    initThreeJS() {
        if (!window.THREE) {
            throw new Error('Three.js is not loaded');
        }

        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0xA9A9A9);

        this.camera = new THREE.PerspectiveCamera(
            60, // Угол обзора
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );

        // Позиция камеры - снизу (y = -2) и сзади (z = 3)
        this.camera.position.set(0, 0, 0);

        // Направляем камеру на центр сцены (0, 0, 0)
        this.camera.lookAt(0, 0, 0);

        this.renderer = new THREE.WebGLRenderer({ antialias: true });
        this.renderer.setSize(window.innerWidth * 0.8, window.innerHeight * 0.8);
        this.renderer.setPixelRatio(window.devicePixelRatio);
        this.container.insertBefore(this.renderer.domElement, this.container.firstChild);

        if (typeof THREE.OrbitControls !== 'undefined') {
            this.controls = new THREE.OrbitControls(this.camera, this.renderer.domElement);
            this.controls.enableDamping = true;
            this.controls.dampingFactor = 0.25;

            this.controls.target.set(0, 0, 0);

            this.controls.minPolarAngle = 0;
            this.controls.maxPolarAngle = Math.PI;

            this.controls.update();
        } else {
            console.warn('OrbitControls not available - camera controls disabled');
        }
    }

    setupLighting() {
        const ambientLight = new THREE.AmbientLight(0xffffff, 0.4);
        this.scene.add(ambientLight);

        const directionalLight = new THREE.DirectionalLight(0xffffff, 0.6);
        directionalLight.position.set(1, 2, 1);
        this.scene.add(directionalLight);


        const fillLight = new THREE.HemisphereLight(0xffffff, 0x444444, 0.2);
        fillLight.position.set(1, 5, 1);
        this.scene.add(fillLight);
    }

    async loadModel() {
        return new Promise((resolve, reject) => {
            const modelUrl = `${this.modelPath}?v=${Date.now()}`;
            console.log(`Loading model from: ${modelUrl}`);

            const loader = new THREE.GLTFLoader();
            loader.load(
                modelUrl,
                (gltf) => {
                    console.log('Model loaded successfully. Contents:');

                    gltf.scene.traverse(child => {
                        if (child.isMesh) {
                            console.log(`Mesh: ${child.name}`, {
                                hasUVs: !!child.geometry.attributes.uv,
                                material: child.material?.name
                            });
                        }
                    });

                    if (this.model) this.scene.remove(this.model);
                    this.model = gltf.scene;
                    this.scene.add(this.model);
                    this.centerModel();
                    resolve();
                },
                undefined,
                error => {
                    console.error('Model loading error:', error);
                    reject(error);
                }
            );
        });
    }

    centerModel() {
        if (!this.model) return;

        const box = new THREE.Box3().setFromObject(this.model);
        const center = box.getCenter(new THREE.Vector3());
        const size = box.getSize(new THREE.Vector3());

        this.model.position.sub(center);

        const maxDim = Math.max(size.x, size.y, size.z);
        const fov = this.camera.fov * (Math.PI / 180);
        let cameraZ = Math.abs(maxDim / (2 * Math.tan(fov / 2))) * 1.5;

        const ratio = 3 / Math.sqrt(2*2 + 3*3);
        cameraZ = Math.max(cameraZ, 3);

        this.camera.position.set(
            0,
            -2 * (cameraZ / 3),
            cameraZ
        );

        this.camera.near = maxDim / 100;
        this.camera.far = maxDim * 50;
        this.camera.updateProjectionMatrix();

        this.camera.lookAt(0, 0, 0);

        if (this.controls) {
            this.controls.target.set(0, 0, 0);
            this.controls.update();
        }

        console.log('Model centered. Camera position:', this.camera.position);
    }

    async applyDesignToModel() {
        if (!this.model) return;

        try {
            const frontTexture = await this.createTextureFromCanvas('front');
            const backTexture = await this.createTextureFromCanvas('back');

            const baseColor = new THREE.Color(0xab9b8c);

            const configureTexture = (texture) => {
                if (!texture) return null;
                texture.flipY = false;
                texture.wrapS = THREE.ClampToEdgeWrapping;
                texture.wrapT = THREE.ClampToEdgeWrapping;
                texture.repeat.set(1, 1);
                texture.offset.set(0, 0);
                return texture;
            };

            this.model.traverse((child) => {
                if (child.isMesh) {
                    if (child.name.includes('front')) {
                        child.material = new THREE.MeshStandardMaterial({
                            map: configureTexture(frontTexture),
                            color: baseColor,
                            roughness: 0.7,
                            metalness: 0.0,
                            side: THREE.DoubleSide,
                            transparent: true
                        });
                    }
                    else if (child.name.includes('back')) {
                        child.material = new THREE.MeshStandardMaterial({
                            map: configureTexture(backTexture),
                            color: baseColor,
                            roughness: 0.7,
                            metalness: 0.0,
                            side: THREE.DoubleSide,
                            transparent: true
                        });
                    }
                    else {
                        child.material = new THREE.MeshStandardMaterial({
                            color: baseColor,
                            roughness: 0.7,
                            side: THREE.DoubleSide
                        });
                    }
                }
            });

        } catch (error) {
            console.error('Error applying design:', error);
        }
    }


    async createTextureFromCanvas(side) {
        try {
            const canvasArea = document.getElementById(`${side}-canvas-area`);
            if (!canvasArea) {
                console.warn(`${side} canvas area not found`);
                return null;
            }

            const canvas = document.createElement('canvas');
            const ctx = canvas.getContext('2d');

            canvas.width = 2048;
            canvas.height = 2048;

            ctx.fillStyle = '#ffffff';
            ctx.fillRect(0, 0, canvas.width, canvas.height);

            const elements = canvasArea.querySelectorAll('.canvas-element');

            const canvasAreaWidth = canvasArea.offsetWidth;
            const canvasAreaHeight = canvasArea.offsetHeight;
            const scaleX = canvas.width / canvasAreaWidth;
            const scaleY = canvas.height / canvasAreaHeight;

            elements.forEach(element => {
                const rect = element.getBoundingClientRect();
                const canvasRect = canvasArea.getBoundingClientRect();

                const x = (rect.left - canvasRect.left) * scaleX;
                const y = (rect.top - canvasRect.top) * scaleY;
                const width = rect.width * scaleX;
                const height = rect.height * scaleY;

                if (element.dataset.type === 'image') {
                    const img = element.querySelector('img');
                    if (img && img.complete) {
                        ctx.save();
                        ctx.globalCompositeOperation = 'source-over';
                        ctx.drawImage(img, x, y, width, height);
                        ctx.restore();
                    }
                } else if (element.dataset.type === 'text') {
                    const span = element.querySelector('span');
                    if (span) {
                        ctx.font = `${parseInt(span.style.fontSize) * scaleX}px ${span.style.fontFamily}`;
                        ctx.fillStyle = span.style.color || '#000000';
                        ctx.textBaseline = 'top';
                        ctx.fillText(span.textContent, x, y);
                    }
                }
            });

            const texture = new THREE.CanvasTexture(canvas);
            texture.flipY = false;
            texture.encoding = THREE.sRGBEncoding;

            return texture;

        } catch (error) {
            console.error(`Error creating ${side} texture:`, error);
            return null;
        }
    }

    setupEventListeners() {
        window.addEventListener('resize', this.handleResize.bind(this));

    }

    handleResize() {
        if (this.camera && this.renderer) {
            this.camera.aspect = window.innerWidth / window.innerHeight;
            this.camera.updateProjectionMatrix();
            this.renderer.setSize(window.innerWidth * 0.8, window.innerHeight * 0.8);
        }
    }

    startAnimation() {
        const animate = () => {
            this.animationId = requestAnimationFrame(animate);

            if (this.controls) {
                this.controls.update();
            }

            if (this.renderer && this.scene && this.camera) {
                this.renderer.render(this.scene, this.camera);
            }
        };
        animate();
    }

    showError(message = 'Failed to load 3D preview') {
        if (this.container) {
            const errorDiv = document.createElement('div');
            errorDiv.style.color = 'white';
            errorDiv.style.textAlign = 'center';
            errorDiv.style.marginTop = '20px';
            errorDiv.textContent = message;
            this.container.appendChild(errorDiv);
        }
    }

    closePreview() {
        if (this.animationId) {
            cancelAnimationFrame(this.animationId);
        }

        if (this.controls) {
            this.controls.dispose();
        }

        if (this.renderer) {
            this.renderer.dispose();
        }

        if (this.container && this.container.parentNode) {
            document.body.removeChild(this.container);
        }

        window.removeEventListener('resize', this.handleResize);
    }
}

document.addEventListener('DOMContentLoaded', () => {
    if (typeof EDITOR_CONFIG !== 'undefined') {
        window.preview3D = new Preview3D(EDITOR_CONFIG);
        window.editor = new GraphicEditor(EDITOR_CONFIG);

        const previewBtn = document.getElementById('preview-btn');
        if (previewBtn) {
            previewBtn.addEventListener('click', async (e) => {
                e.preventDefault();
                try {
                    previewBtn.disabled = true;
                    previewBtn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Загрузка...';
                    await window.preview3D.show3dPreview();
                } catch (error) {
                    console.error('3D Preview error:', error);
                    alert('Ошибка при создании 3D превью');
                } finally {
                    previewBtn.disabled = false;
                    previewBtn.innerHTML = '<i class="fas fa-cube"></i> 3D Превью';
                }
            });
        }
    }
});