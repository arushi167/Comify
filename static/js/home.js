document.addEventListener('DOMContentLoaded', function() {
    var topicInput = document.getElementById('topic');
    var characterCount = document.getElementById('text_count');
    var submitBtn = document.getElementById("submit_btn");

    topicInput.addEventListener('input', function() {
        var maxLength = 70;
        var currentLength = topicInput.value.length;

        if (currentLength > maxLength) {
            topicInput.value = topicInput.value.substring(0, maxLength);
            currentLength = maxLength;
        }

        // Update the character count
        characterCount.textContent = currentLength + '/' + maxLength;
    });

    topicInput.addEventListener("keypress", function(event) {
        if (event.key === "Enter") {
            generateContent();
        }
    });

    submitBtn.addEventListener("click", function() {
        generateContent();
    });

    function generateContent() {
        const topic = topicInput.value;
        const comic_style = document.getElementById("comic_style").value;
        const comic_language = document.getElementById("comic_language").value;
        window.location.href=`/loading?topic=${encodeURIComponent(topic)}&comic=${encodeURIComponent(comic_style)}&lang=${encodeURIComponent(comic_language)}`     
    }

});