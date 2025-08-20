  document.addEventListener("DOMContentLoaded", function () {
    const slides = document.querySelectorAll("[data-slide]");
    let current = 0;

    function showSlide(index) {
      slides.forEach((slide, i) => {
        if (i === index) {
          slide.classList.remove("opacity-0");
          slide.classList.add("opacity-100");
        } else {
          slide.classList.remove("opacity-100");
          slide.classList.add("opacity-0");
        }
      });
    }

    function nextSlide() {
      current = (current + 1) % slides.length;
      showSlide(current);
    }

    showSlide(0);
    setInterval(nextSlide, 4000);
  });
