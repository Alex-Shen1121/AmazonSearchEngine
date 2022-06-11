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
    query = request.form['query']  # 从web的输入框中获取用户输入的query
    keys_list, doc_id_list, doc_sim_list, page_list = SE.search_query(query)
    try:
        checked = ['checked="true"', '']
        query = request.form['query']  # 从web的输入框中获取用户输入的query
        if query != '':
            start = time.perf_counter()
            keys_list, doc_id_list, doc_sim_list, page_list = SE.search_query(query)
            if len(doc_id_list) == 0:
                return render_template('search.html', key=query, error=False)
            else:
                docs_list = get_doc_from_docID(doc_id_list)
                docs_now = docs_list[0:5]
                end = time.perf_counter()
                cost = round(end - start, 3)
                return render_template('high_search.html', checked=checked, key=query, keys_list=keys_list,
                                       docs=docs_now, page=page_list, cost=cost, error=True)
        else:
            return render_template('search.html', error=False)
    except:
        print('search error')


# 将需要的数据以字典形式打包传递给search函数
def get_doc_from_docID(docid, extra=False):
    docs = []
    i = 0
    for id in docid:
        title = SE.index_class.origin_doc_set[id]['title']
        body = SE.index_class.origin_doc_set[id]['content']
        snippet = body[0:180] + '……'
        time = str(SE.index_class.origin_doc_set[id]['datetime']).split(' ')[0]
        datetime = SE.index_class.origin_doc_set[id]['datetime']
        sim = doc_sim_list[i]
        i += 1
        doc = {'title': title, 'snippet': snippet, 'datetime': datetime, 'time': time, 'body': body,
               'id': id, 'sim': sim, 'extra': []}
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
        keys_list, doc_id_list, doc_sim_list, page_list = SE.search_query(query, selected)
        if len(doc_id_list) == 0:
            return render_template('search.html', key=query, error=False)
        else:
            docs_list = get_doc_from_docID(doc_id_list)
            docs_now = docs_list[0:5]
            end = time.perf_counter()
            cost = round(end - start, 3)
            return render_template('high_search.html', checked=checked, key=query, keys_list=keys_list, docs=docs_now,
                                   page=page_list, cost=cost, error=True)
    except:
        print('high search error')


@app.route('/search/<id>/', methods=['GET', 'POST'])
def content(id):
    id = int(id)
    try:
        doc = get_doc_from_docID([id])
        return render_template('content.html', doc=doc[0])
    except:
        print('content error')


if __name__ == '__main__':
    # SE = SearchEngine('whole')
    SE = SearchEngine('test')

    # app.run(host="0.0.0.0", port=1234)  # 部署到服务器上，局域网内可通过服务器IP和端口访问
    app.run(host="localhost", port=1234)  # 部署在本地
