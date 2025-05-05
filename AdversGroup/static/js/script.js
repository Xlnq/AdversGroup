let currentImageIndex = 0;
const images = document.querySelectorAll('.gallery-slide img');

function showImage(index) {
    images.forEach((img, i) => {
        img.classList.toggle('active', i === index);
    });
}

function nextImage() {
    currentImageIndex = (currentImageIndex + 1) % images.length;
    showImage(currentImageIndex);
}

function prevImage() {
    currentImageIndex = (currentImageIndex - 1 + images.length) % images.length;
    showImage(currentImageIndex);
}

// Показываем первое изображение при загрузке
document.addEventListener('DOMContentLoaded', () => {
    showImage(currentImageIndex);
    setInterval(nextImage, 5000);
});
