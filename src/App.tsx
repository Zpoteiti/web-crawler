export default function App() {
  return (
    <div className="bg-blue-500 text-white p-8 min-h-screen">
      <h1 className="text-4xl font-bold mb-4">立讯AI聊天界面测试</h1>
      <div className="bg-white text-black p-4 rounded-lg shadow-lg max-w-md mb-6">
        <p className="text-lg mb-2">Tailwind CSS 测试</p>
        <p className="text-sm text-gray-600">如果您看到蓝色背景和白色卡片，说明样式正常工作！</p>
        <button className="mt-4 bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
          测试按钮
        </button>
      </div>
      
      <div className="bg-white text-black rounded-lg p-6 max-w-4xl">
        <div className="flex gap-6">
          <div className="bg-gray-100 w-64 p-4 rounded">
            <div className="bg-blue-500 text-white px-4 py-2 rounded mb-4">开启新对话</div>
            <div className="space-y-2">
              <div className="text-sm">翻译多语言互译项目报告</div>
              <div className="text-sm">出差该怎么申请</div>
              <div className="text-sm">五险一金是怎么发放的</div>
            </div>
          </div>
          
          <div className="flex-1">
            <div className="text-center mb-6">
              <div className="w-12 h-12 bg-gradient-to-br from-blue-400 to-purple-500 rounded-lg mx-auto mb-4"></div>
              <h2 className="text-xl font-semibold mb-2">Hello! 我是立讯技术百事通</h2>
              <p className="text-gray-600">有什么问题欢迎咨询</p>
            </div>
            
            <div className="grid grid-cols-2 gap-4">
              <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-4 rounded-lg border border-blue-100">
                <h3 className="font-semibold mb-2">近期热搜</h3>
                <p className="text-sm text-gray-600 mb-3">深度搜索您关心的问题</p>
                <div className="space-y-1 text-sm">
                  <div>1. 工作中遇到棘手问题怎么办</div>
                  <div>2. 国务院发布的2025年法定节假日安排</div>
                  <div>3. 如何锻炼身体</div>
                </div>
              </div>
              
              <div className="bg-gradient-to-br from-purple-50 to-pink-50 p-4 rounded-lg border border-purple-100">
                <h3 className="font-semibold mb-2">知识工坊</h3>
                <p className="text-sm text-gray-600 mb-3">办公学习必备</p>
                <div className="space-y-2">
                  <div className="bg-white p-2 rounded flex items-center">
                    <div className="w-6 h-6 bg-gradient-to-br from-blue-400 to-purple-400 rounded mr-2"></div>
                    <span className="text-sm">翻译</span>
                  </div>
                  <div className="bg-white p-2 rounded flex items-center">
                    <div className="w-6 h-6 bg-gradient-to-br from-blue-400 to-purple-400 rounded mr-2"></div>
                    <span className="text-sm">总结</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
} 