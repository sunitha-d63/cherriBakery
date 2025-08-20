
  const container = document.getElementById("testimonialContainer");
  const scrollRightBtn = document.getElementById("scrollRightBtn");


  scrollRightBtn.addEventListener("click", () => {
    container.scrollBy({ left: 300, behavior: "smooth" });
  });

  let isDown = false;
  let startX, scrollLeft;

  container.addEventListener("mousedown", (e) => {
    isDown = true;
    startX = e.pageX - container.offsetLeft;
    scrollLeft = container.scrollLeft;
  });

  container.addEventListener("mouseleave", () => (isDown = false));
  container.addEventListener("mouseup", () => (isDown = false));

  container.addEventListener("mousemove", (e) => {
    if (!isDown) return;
    e.preventDefault();
    const x = e.pageX - container.offsetLeft;
    const walk = (x - startX) * 2; 
    container.scrollLeft = scrollLeft - walk;
  });

