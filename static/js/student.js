function scrollToFeedback() {
    const section = document.getElementById("feedback-section");
    section.classList.remove("hidden");
    section.scrollIntoView({ behavior: "smooth" });
}