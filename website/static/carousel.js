document.addEventListener('DOMContentLoaded', function() {
    
    const carouselItems = document.querySelectorAll('[data-carousel-item]');
    const prevButton = document.querySelector('[data-carousel-prev]');
    const nextButton = document.querySelector('[data-carousel-next]');
    
   
    let currentIndex = 0;
    
    
    if (carouselItems.length > 0) {
        carouselItems[0].classList.remove('hidden');
    }
    
   
    function updateSlides() {
        carouselItems.forEach((item, index) => {
            if (index === currentIndex) {
                item.classList.remove('hidden');
            } else {
                item.classList.add('hidden');
            }
        });
    }
    
   
    if (prevButton) {
        prevButton.addEventListener('click', function() {
            currentIndex = (currentIndex - 1 + carouselItems.length) % carouselItems.length;
            updateSlides();
        });
    }
    
   
    if (nextButton) {
        nextButton.addEventListener('click', function() {
            currentIndex = (currentIndex + 1) % carouselItems.length;
            updateSlides();
        });
    }
    
    // Auto-advance slides every 5 seconds
    setInterval(function() {
        currentIndex = (currentIndex + 1) % carouselItems.length;
        updateSlides();
    }, 5000);
});