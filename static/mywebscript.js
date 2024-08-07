let RunSentimentAnalysisZomato = () =>{
    urlToAnalyzeZomato = document.getElementById("urlToAnalyzeZomato").value;

    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("system_response_zomato").innerHTML = xhttp.responseText;
        }
    };
    xhttp.open("GET", "zomatoReviewDetector?urlToAnalyzeZomato="+urlToAnalyzeZomato, true);
    xhttp.send();
}

let RunNutritionEstimation = () =>{
    inputToAnalyze = document.getElementById("inputToAnalyze").value;

    let xhttp = new XMLHttpRequest();
    xhttp.onreadystatechange = function() {
        if (this.readyState === 4 && this.status === 200) {
            document.getElementById("system_response_nutrition").innerHTML = xhttp.responseText;
        }
    };
    xhttp.open("GET", "nutritionEstimator?inputToAnalyze="+inputToAnalyze, true);
    xhttp.send();
}