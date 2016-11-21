from xml.etree.ElementTree import tostring

from flask import Flask, Response

from parsing.config import Config
from parsing.parse import Parser
from ucca.convert import from_text, to_standard
from ucca.textutil import indent_xml

app = Flask(__name__)
config = Config()
parser = Parser(config.args.model, config.args.classifier)


@app.route("/parse")
def parse():
    text = request.values["input"]
    in_passage = from_text(text)
    out_passage = parser.parse(in_passage)
    root = to_standard(out_passage)
    xml = tostring(root).decode()
    response = indent_xml(xml)
    return Response(response, mimetype="text/xml")

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
