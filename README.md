# AmazonSearchEngine
## 基于倒排索引算法的搜索引擎设计

演示网址：[https://www.codingshen.com/SearchEngine](https://www.codingshen.com/SearchEngine)

界面截图：
首页：
<img width="1260" alt="image" src="https://user-images.githubusercontent.com/73343630/203271254-1920c176-389c-4fbb-8baa-28f12e38b153.png">
搜索界面：
<img width="883" alt="image" src="https://user-images.githubusercontent.com/73343630/203271407-7b7d9eb2-1937-4aeb-87d2-b82587cd9acc.png">


系统功能介绍：
一. 基本功能：
(1) 使用开源的 stemming 程序把“reviewText”、“summary”、“title”、“feature”、 “description”等中的 tokens 转换成 terms。
(2) 数据统计：以构建倒排索引的文档为基础，检验 Heaps’ law 和 Zipf’s law 在该数 据集上是否正确，要求以曲线图或表格的方式来呈现，包含定量的结果。
(3) 开发的信息检索系统：要求支持基本的用户交互，包括输入框和返回结果的呈现 （包含超链接跳转），界面简洁美观。
(4) 开发的信息检索系统 ： 要求使用倒排索引（inverted index）, 不能使用SQL Server、MySQL等数据库中的关系表来存储数据，并分析倒排索引构建的时间复 杂度和空间复杂度。
(5) 开发的信息检索系统：要求使用 TF-IDF 作为权重的计算方式，在报告中包含相关 的数学公式。要求使用公式编辑工具，不能截图，并对公式中的符号做出解释， 对相关的代码实现给出详细的注释，并分析该部分的时间复杂度。
(6) 开发的信息检索系统：要求使用余弦相似度作为<query,document>的相关性分值 的计算方式，在报告中包含相关的数学公式。要求使用公式编辑工具，不能截图， 并对公式中的符号做出解释，对相关的代码实现给出详细的注释（如在实现中做 了某种简化或修改需要明确说明），并分析该部分的时间复杂度。
(7) 开发的信息检索系统：要求根据相关性分值的大小对匹配到的 documents 进行排 序，返回 top 5 的结果（要求同时显示每个返回的 document 的相关性的分值信息）。 需要特别注意效率问题，要求在查询结果的上方显示查询的耗时（单位秒，保留 小数点后两位）。

二. 特色功能：
(1) 数据规模大。例如，使用了 Gift_Cards.json，而非 Gift_Cards_5.json。
(2) 支持按域检索功能。应至少包含 3 个不同的“域”，如“title”、“reviewText”、 “feature”等。
(3) 支持较为友好的用户交互，例如通过字体标红等方式帮助用户快速理解返回的结 果。
(4) 在 对返回的结果进行排序 时 ， 考虑 除 余弦相似度 之外 的 其他 合理 因素 ， 如 document 的“vote”等。需要明确说明所采取的具体方式。
(5) 支持 query 建议（方法不限于教材中的方法）。能够给出 1-3 个合理的候选 query。
(6) 支持 query 纠错（方法不限于教材中的方法）。能够发现 query 中错误的 term， 并给出 1-3 个正确的候选 query。
