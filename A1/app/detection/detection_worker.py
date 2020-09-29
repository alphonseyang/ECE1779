from flask import render_template, request

from FaceMaskDetection import pytorch_infer


def work():
    if request.method == "POST":
        print(1)

    pytorch_infer.main("../../FaceMaskDetection/test/test1.jpeg", "../../FaceMaskDetection/test/output1.jpeg")
    return render_template("detection.html")
