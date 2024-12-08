from paddlex import create_pipeline

pipeline = create_pipeline(pipeline="formula_recognition")

output = pipeline.predict("sample_img.png")
for res in output:
    res.print()
    res.save_to_img("./output/")