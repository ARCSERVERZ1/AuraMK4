// location_logger.js

document.addEventListener("DOMContentLoaded", function() {

    // Helper function to send the payload to your API
    function sendLocationToApi(lat, lng) {
        const payload = {
            user: window.AppConfig.user,
            latitude: lat,
            longitude: lng,
        };

        fetch('/aura_standard/', {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-CSRFToken": window.AppConfig.csrfToken // Required by Django
            },
            body: JSON.stringify(payload)
        })
        .then(response => {
            if (response.ok) {
                console.log("Location successfully logged to API.");
            } else {
                console.error("API returned an error:", response.status);
            }
        })
        .catch(error => {
            console.error("Network error while calling API:", error);
        });
    }

    // 1. Check if the browser supports geolocation
    if ("geolocation" in navigator) {
        // 2. Request the current coordinates
        navigator.geolocation.getCurrentPosition(
            function(position) {
                // Success: Send actual latitude and longitude
                sendLocationToApi(position.coords.latitude, position.coords.longitude);
            },
            function(error) {
                // If user denies permission, use fallback test data so you can still test locally
                console.warn("Geolocation failed (" + error.message + "). Using local test coordinates.");
                sendLocationToApi(1234, 34567);
            },
            {
                enableHighAccuracy: true,
                timeout: 10000,
                maximumAge: 0
            }
        );
    } else {
        // Fallback if browser doesn't support geolocation at all
        console.warn("Geolocation is not supported by this browser. Using test coordinates.");
        sendLocationToApi(1234, 34567);
    }
});