from flask import Flask, render_template, request
from ReviewAnalysis.review_detection import ReviewDetection
from NutritionEstimator.nutrition_estimation import NutritionEstimation
app = Flask("Review Detector")
@app.route('/zomatoReviewDetector')
def zomato_rev_detector():
    url_to_analyze = request.args.get('urlToAnalyzeZomato')
    result = ReviewDetection(url_to_analyze).review_zomato_detector()
    num_pos_reviews = result['general_sentiment']['positive_reviews']
    num_mixed_reviews = result['general_sentiment']['mixed_reviews']
    num_neg_reviews = result['general_sentiment']['negative_reviews']
    complaints = {}
    complements = {}
    for target in result['complaints'].keys():
        temp = result['complaints'][target]
        complaints[target] = "Users have made " + str(temp['count']) + " complaint(s) about " + target + " specifically saying that it's " + ", ".join([detail[0] for detail in temp['details']])
    for target in result['complements'].keys():
        temp = result['complements'][target]
        complements[target] = "Users have made " + str(temp['count']) + " complement(s) about " + target + " specifically saying that it's " + ", ".join([detail[0] for detail in temp['details']])

    st_complain = ""
    st_complement = ""
    for complaint in complaints.values():
        st_complain += complaint + "<br>"
    for complement in complements.values():
        st_complement += complement + "<br>"
    gen_sent = "We have " + str(num_pos_reviews) + " positive reviews, " + str(num_mixed_reviews) + " mixed reviews, and " + str(num_neg_reviews) + " negative reviews. <br> "



    return  gen_sent + "<br>" + st_complain + "<br>" + st_complement + "<br>" + "Location Details:" + "<br>" + result["Location Details"] + "<br>" + "Product Details:" + "<br>" + result["Product Details"] + "<br>" + "Skill Details:" + "<br>" + result["Skill Details"] + "<br>" + "Staff Details:" + "<br>" + result["Person Details"]

@app.route('/nutritionEstimator')
def nutrition_estimator():
    input_to_analyze = request.args.get('inputToAnalyze')
    result = NutritionEstimation(input_to_analyze).generate_facts()
    return result
@app.route("/")
def render_index_page():
    '''renders home page'''
    return render_template('index.html')

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)
