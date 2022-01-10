from flask import Flask, render_template, request
app = Flask(__name__)

from pymongo import MongoClient
client = MongoClient('localhost', 27017)
db = client.dasparta

## 메인페이지
@app.route('/')
def home():

    return render_template('mainPage.html')

@app.route('/detail', methods=['GET'])
def read_reviews():
    board_title = request.args.get('title')
    board_info = db.childcare.find_one({'title': '@@아파트 아이 품앗이'}, {'_id': False})

    return render_template('detail.html', title=board_info['title'],location=board_info['location'], cur_cnt=board_info['cur_cnt'], population=board_info['population'],desc=board_info['desc'])

if __name__ == '__main__':
    app.run('0.0.0.0', port=5000, debug=True)