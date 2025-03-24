document.addEventListener("DOMContentLoaded", function () {
    function updateCountdowns() {
        const countdownElements = document.querySelectorAll(".countdown-timer");
        const now = Math.floor(Date.now() / 1000); // Current time in seconds

        countdownElements.forEach((el) => {
            const endTime = parseInt(el.getAttribute("data-endtime"), 10);
            let remainingTime = endTime - now;

            if (remainingTime <= 0) {
                el.textContent = "Auction Ended";
                el.classList.add("text-danger"); // Make it visually distinct
                return;
            }

            let hours = Math.floor(remainingTime / 3600);
            let minutes = Math.floor((remainingTime % 3600) / 60);
            let seconds = remainingTime % 60;

            el.textContent = `${String(hours).padStart(2, '0')}:${String(minutes).padStart(2, '0')}:${String(seconds).padStart(2, '0')}`;
        });
    }

    updateCountdowns(); // Initial call
    setInterval(updateCountdowns, 1000); // Update every second
});
