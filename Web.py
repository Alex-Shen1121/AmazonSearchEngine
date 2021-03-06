from unicodedata import category

from numpy import imag
from SearchEngine import SearchEngine
from flask import Flask, render_template, request
import time

app = Flask(__name__)

global query
global checked
global page_list
global doc_id_list
global doc_sim_list
global docs_list
global keys_list
global docs_now
global cost


# 主页
@app.route('/')
def main():
    return render_template('search.html', key=None, error=True)


# 读取表单数据，获得doc_ID
@app.route('/search/', methods=['POST'])
def search():
    global query
    global checked
    global page_list
    global doc_id_list
    global doc_sim_list
    global docs_list
    global keys_list
    global docs_now
    global cost
    # query = request.form['query']  # 从web的输入框中获取用户输入的query
    # keys_list, doc_id_list, doc_sim_list, page_list = SE.search_query(query)
    try:
        checked = ['checked="true"', '']
        query = request.form['query']  # 从web的输入框中获取用户输入的query
        if query != '':
            start = time.perf_counter()
            keys_list, doc_id_list, doc_sim_list, page_list, query_advice = SE.search_query(
                query)
            if len(doc_id_list) == 0:
                queryCorrect = query_correct(query)
                return render_template('search.html', key=query, query_correct=queryCorrect, error=False)
            else:
                docs_list = get_doc_from_docID(doc_id_list)
                docs_now = docs_list[0:5]
                end = time.perf_counter()
                cost = round(end - start, 3)
                return render_template('high_search.html', checked=checked, key=query, keys_list=keys_list,
                                       docs=docs_now, page=page_list, query_advice=query_advice, cost=cost, error=True)
        else:
            return render_template('search.html', error=False)
    except:
        print('search error')


def editDistance(s1, s2):
    n, m = len(s1), len(s2)

    # 创建dp数组 size = n * m
    dp = [[0] * (m + 1) for _ in range(n + 1)]

    # 边界状态初始化
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j

     # 计算所有 DP 值
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            # 如果字符相同，则不需要操作 temp = 0
            temp = 0 if s1[i - 1] == s2[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j - 1] + temp,
                           dp[i - 1][j] + 1,
                           dp[i][j - 1] + 1)

    return dp[n][m]


def query_correct(query):
    wordList = SE.index_class.terms_lib
    correctList = {}
    for word in wordList:
        correctList[word] = editDistance(query, word)
    correctList = sorted(correctList.items(), key=lambda x: x[1])
    return [x[0] for x in correctList[:5]]

# 将需要的数据以字典形式打包传递给search函数


def get_doc_from_docID(docid, extra=False):
    docs = []
    i = 0
    for id in docid:
        # 商品标题
        title = SE.index_class.raw_data_metaPlusReview[id]['title']
        # 商品类别
        category = list(
            set(SE.index_class.raw_data_metaPlusReview[id]['category']))
        # 商品描述
        description = list(
            set(SE.index_class.raw_data_metaPlusReview[id]['description']))
        # 商品品牌
        brand = SE.index_class.raw_data_metaPlusReview[id]['brand']
        # 商品特性
        feature = list(
            set(SE.index_class.raw_data_metaPlusReview[id]['feature']))
        # 商品细节
        details = SE.index_class.raw_data_metaPlusReview[id]['details']
        # 商品大类
        main_cat = SE.index_class.raw_data_metaPlusReview[id]['main_cat']
        # 商品价格
        price = SE.index_class.raw_data_metaPlusReview[id]['price']
        # 商品高清图
        imageURLHighRes = list(
            set(SE.index_class.raw_data_metaPlusReview[id]['imageURLHighRes']))
        # 评论时间
        reviews_time = [x['reviewTime']
                        for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # 评论Name
        reviewerName = [x['reviewerName']
                        for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # 商品评论
        reviews_image = [x['image']
                         for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # 评分
        reviews_overall = [x['overall']
                           for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # 点赞数
        reviews_vote = [x['vote']
                        for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # 评论
        reviews_text = [x['reviewText']
                        for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        # summary
        reviews_summary = [x['summary']
                           for x in SE.index_class.raw_data_metaPlusReview[id]['reviews']]
        reviews = [[reviews_image[i], reviews_overall[i], reviews_vote[i],
                    reviews_text[i], reviews_summary[i], reviewerName[i], reviews_time[i]]
                   for i in range(len(reviews_image))]

        sim = doc_sim_list[i]
        i += 1
        doc = {
            'title': title,
            'category': category,
            'description': description,
            'brand': brand,
            'feature': feature,
            'details': details,
            'main_cat': main_cat,
            'price': price,
            'imageURLHighRes': imageURLHighRes,
            'reviewsimage': reviews_image,
            'reviewsoverall': reviews_overall,
            'reviewsvote': reviews_vote,
            'reviewstext': reviews_text,
            'reviewssummary': reviews_summary,
            'reviews': reviews,
            'sim': sim,
            'id': id
        }
        docs.append(doc)
    return docs


@app.route('/search/page/<page_no>/', methods=['GET'])
def next_page(page_no):
    global query
    global checked
    global page_list
    global docs_list
    global keys_list
    global docs_now
    global cost
    try:
        page_no = int(page_no)
        docs_now = docs_list[(page_no - 1) * 5: page_no * 5]
        print(docs_now)
        return render_template('high_search.html', checked=checked, key=query, keys_list=keys_list, docs=docs_now,
                               page=page_list, cost=cost, error=True)
    except:
        print('next error')


@app.route('/search/<key>/', methods=['POST'])
def high_search(key):
    global query
    global checked
    global page_list
    global doc_id_list
    global doc_sim_list
    global docs_list
    global keys_list
    global docs_now
    global cost
    try:
        start = time.perf_counter()
        selected = int(request.form['order'])
        for i in range(2):
            if i == selected:
                checked[i] = 'checked="true"'
            else:
                checked[i] = ''
        keys_list, doc_id_list, doc_sim_list, page_list, query_advice = SE.search_query(
            query, selected)
        if len(doc_id_list) == 0:
            return render_template('search.html', key=query, error=False)
        else:
            docs_list = get_doc_from_docID(doc_id_list)
            docs_now = docs_list[0:5]
            end = time.perf_counter()
            cost = round(end - start, 3)
            return render_template('high_search.html', checked=checked, key=query, query_advice=query_advice, keys_list=keys_list, docs=docs_now,
                                   page=page_list, cost=cost, error=True)
    except:
        print('high search error')


@app.route('/search/<id>/', methods=['GET', 'POST'])
def content(id):
    id = str(id)
    try:
        doc = get_doc_from_docID([id])
        return render_template('content.html', doc=doc[0])
    except:
        print('content error')


if __name__ == '__main__':
    SE = SearchEngine('whole')
    # SE = SearchEngine('test')

    # app.run(host="0.0.0.0", port=1234)  # 部署到服务器上，局域网内可通过服务器IP和端口访问
    app.run(host="localhost", port=1234)  # 部署在本地
