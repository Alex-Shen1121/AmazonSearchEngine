from collections import Counter
from InvertedIndex import InvertIndex
import jieba
import re
import math
import datetime
from nltk.stem import PorterStemmer


class SearchEngine:
    def __init__(self, type = 'test'):
        self.index_class = InvertIndex("./datasets", type)

    # 定义计算cosine similarity的函数
    def cos_sim(self, s1_cut_code, s2_cut_code):
        sum = 0
        sq1 = 0
        sq2 = 0

        # 计算余弦乘积
        for i in range(len(s1_cut_code)):
            sum += s1_cut_code[i] * s2_cut_code[i]
            sq1 += pow(s1_cut_code[i], 2)
            sq2 += pow(s2_cut_code[i], 2)

        # 计算余弦相似度
        try:
            result = round(float(sum) / (math.sqrt(sq1) * math.sqrt(sq2)), 4)
        except ZeroDivisionError:
            result = 0.0

        return result

    # 搜索同时含有term1和term2的文档
    # input：倒排索引(字典)，term1的倒排索引(列表)，term2的倒排索引(列表)
    # output：符合条件的文档id(列表)
    def find_term1_term2(self, l1, l2):
        # 指向term1这条倒排索引的元素的指针（下标）
        p1 = 0
        # 指向term2这条倒排索引的元素的指针（下标）
        p2 = 0
        # term1这条倒排索引的长度
        size1 = len(l1)
        # term2这条倒排索引的长度
        size2 = len(l2)
        # 用于返回结果的列表
        result = []

        # 对这两条倒排索引进行AND操作
        while p1 < size1 and p2 < size2:
            if l1[p1] == l2[p2]:
                result.append(l1[p1])
                p1 += 1
                p2 += 1
            elif l1[p1] < l2[p2]:
                p1 += 1
            else:
                p2 += 1

        return result

    # 根据选择排序的思想，返回cos-sim topK的文档ID，复杂度O(n)
    def top_k_cossim(self, final_result, k = 25):
        doc_id_list = []
        cos_sim_list = []
        time_list = []
        for v in final_result.values():
            doc_id_list.append(v['doc_ID'])
            cos_sim_list.append(v['cos_sim'])

        final_result_k = {}
        for i in range(len(doc_id_list)):
            max_index = i
            for j in range(i + 1, len(doc_id_list)):
                if cos_sim_list[j] > cos_sim_list[max_index]:
                    max_index = j
            if max_index != i:
                temp_id = doc_id_list[i]
                doc_id_list[i] = doc_id_list[max_index]
                doc_id_list[max_index] = temp_id
                temp_cos_sim = cos_sim_list[i]
                cos_sim_list[i] = cos_sim_list[max_index]
                cos_sim_list[max_index] = temp_cos_sim
            final_result_k[i] = {'doc_ID': doc_id_list[i], 'cos_sim': cos_sim_list[i]}
            k -= 1
            if k == 0:
                break

        return final_result_k

    # 根据选择排序的思想，返回time topK的文档ID，复杂度O(n)
    def top_k_vote(self, final_result, k = 25):
        doc_id_list = []
        cos_sim_list = []
        voteSum_list = []
        for v in final_result.values():
            doc_id_list.append(v['doc_ID'])
            cos_sim_list.append(v['cos_sim'])
            voteSum_list.append(v['vote_sum'])

        k = 25
        final_result_k = {}
        for i in range(len(doc_id_list)):
            max_index = i
            for j in range(i + 1, len(doc_id_list)):
                if voteSum_list[j] > voteSum_list[max_index]:
                    max_index = j
            if max_index != i:
                temp_id = doc_id_list[i]
                doc_id_list[i] = doc_id_list[max_index]
                doc_id_list[max_index] = temp_id
                temp_cos_sim = cos_sim_list[i]
                cos_sim_list[i] = cos_sim_list[max_index]
                cos_sim_list[max_index] = temp_cos_sim
            final_result_k[i] = {'doc_ID': doc_id_list[i], 'cos_sim': cos_sim_list[i]}
            k -= 1
            if k == 0:
                break

        return final_result_k

    # 搜索与字符串query相关的文档
    def search_query(self, search_query, sort_type=0):
        # 将大写字母转成小写
        search_query = search_query.lower()
        # 用正则表达式去除标点，只保留"中文"、"大小写英文字母"、"数字"
        search_query = re.sub("[^\u4e00-\u9fa5^a-z^A-Z^0-9]", " ", search_query)
        # jieba分词，禁用全切割模式
        tokens_list = list(jieba.cut(search_query, cut_all=False))
        tokens_list = list(filter(lambda x: x != '', tokens_list))
        tokens_list = list(filter(lambda x: x != ' ', tokens_list))
        terms_list = list(set(tokens_list))
        ps = PorterStemmer()
        terms_list = [ps.stem(x) for x in terms_list]
        # 输出query解析结果
        print("查询字符串的解析结果：" + str(terms_list))

        # 在倒排索引中，逐个找出包含这些terms的文档id，并求出它们的交集作为结果
        # 如果某个term在倒排索引中没有，则跳过这个term继续。这样可以避免因为某些term找不到而导致整个query没有返回结果
        # 例如：一个query=“中国深圳徐宇明”，这个query经过解析得到的结果为“中国”、“深圳”、“徐宇明”
        # 而在倒排索引中，“中国”=[0,15,20]、“深圳”=[0,15,18]、“徐宇明”=没有这个term
        # 那么返回的结果是“中国”∩“深圳”=[0,15]
        # （因为“徐宇明”这个term没有在索引中出现，所以直接跳过。如果我们硬要加入“徐宇明”，那么返回的结果将会=[]，这不合理。）
        try:
            result = self.index_class.invert_index[terms_list[0]]
        except:
            result = []

        # 做查询结果的交集
        for i in range(1, len(terms_list)):
            try:
                result = self.find_term1_term2(result, self.index_class.invert_index[terms_list[i]])
            except:
                continue

        # 计算query文本的TFIDF向量
        # 计算query_TF
        query_TF = [0.0] * self.index_class.terms_num
        for token in tokens_list:
            if token in self.index_class.terms_lib:
                query_TF[self.index_class.terms_lib.index(token)] += 1.0
        i = 0
        for frequency in query_TF:
            if frequency > 0:
                query_TF[i] = (1 + math.log(query_TF[i], 10))
            else:
                query_TF[i] = 0
            i += 1

        # 计算query_TFIDF
        query_TFIDF = [0.0] * self.index_class.terms_num
        for i in range(self.index_class.terms_num):
            query_TFIDF[i] = query_TF[i] * self.index_class.doc_IDF[i]

        # 计算与获取query与搜索到的document(s)之间的cos-sim、时间；并整合成一个字典，作为结果进行返回
        final = {}
        for i in range(len(result)):
            doc_id = result[i]
            doc_TFIDF = self.index_class.doc_TFIDF[doc_id]
            sim = self.cos_sim(query_TFIDF, doc_TFIDF)
            vote_sum = len(self.index_class.raw_data_metaPlusReview[doc_id]['reviews'])
            for review in self.index_class.raw_data_metaPlusReview[doc_id]['reviews']:
                vote_sum += int(review['vote'])
            final[i] = {'doc_ID': doc_id, 'cos_sim': sim, 'vote_sum': vote_sum}

        # 根据用户选择的方式排序返回
        if sort_type == 0:
            final = self.top_k_cossim(final, k=25)  # 按余弦相似度
        else:
            final = self.top_k_vote(final, k=25)  # 按发布时间

        # 页数（每页5个）
        if len(final) <= 5:
            page_list = [1]
        else:
            page_list = range(1, len(final) // 5 + 1)

        doc_id_list = []
        doc_sim_list = []
        for d in final.values():
            doc_id_list.append(d["doc_ID"])
            doc_sim_list.append(d["cos_sim"])

        wordlist = []
        for docID in result:
            for words in self.index_class.doc_set[docID].values():
                wordlist.extend(words)
        wordlist = Counter(wordlist)
        wordlist = sorted(wordlist.items(), key=lambda x: x[1], reverse=True)
        query_advice = [x[0] for x in wordlist[:5]]
        return terms_list, doc_id_list, doc_sim_list, page_list, query_advice

if __name__ == '__main__':
    # 初始化索引类
    se = SearchEngine('test')