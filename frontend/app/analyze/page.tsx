"use client";

import { useState } from "react";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress"; // 需要安装 progress 组件
import { Shield, Activity, Package, Sword, UploadCloud, Mic, Target, Zap, Settings } from "lucide-react";
import { toast } from "sonner";

export default function AnalyzePage() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);

  // 处理文件上传
  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;

    setLoading(true);
    setResult(null);
    
    const formData = new FormData();
    formData.append("file", file);

    try {
      const res = await fetch("/api/analyze", {
        method: "POST",
        body: formData,
      });
      const data = await res.json();

      if (data.status === "success") {
        setResult(data.data);
        toast.success("分析完成");
      } else {
        toast.error("分析失败");
      }
    } catch (err) {
      toast.error("网络错误");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex min-h-screen font-sans">
      
      {/* 侧边栏 (保持统一) */}
      <aside className="w-64 p-6 flex flex-col fixed h-full glass border-r border-white/5 z-50">
        <div className="flex items-center gap-3 mb-10 px-2">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Shield className="text-white w-5 h-5" />
            </div>
            <span className="font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">武器管理系统</span>
        </div>
        <nav className="space-y-1 flex-1">
            <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
                <Link href="/dashboard"><Activity className="mr-2 h-4 w-4" /> 控制台</Link>
            </Button>
            <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
                <Link href="/catalog"><Package className="mr-2 h-4 w-4" /> 武器库</Link>
            </Button>
            {/* 当前页高亮 */}
            <Button asChild variant="ghost" className="w-full justify-start text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all duration-200">
                <Link href="/analyze"><Sword className="mr-2 h-4 w-4" /> AI 识别</Link>
            </Button>
            <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
                <Link href="/admin">
                    <Settings className="mr-2 h-4 w-4" />
                    系统管理
                </Link>
            </Button>
        </nav>
      </aside>

      {/* 主内容 */}
      <main className="flex-1 p-8 ml-64">
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">声纹战术分析</h1>
          <p className="text-zinc-400">上传战场录音，系统将自动进行端云混合推理</p>
        </header>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
          
          {/* 左侧：上传区 */}
          <Card className="glass-card h-fit">
            <CardHeader>
              <CardTitle className="flex items-center gap-2 text-zinc-200">
                <UploadCloud className="w-5 h-5 text-blue-500" />
                信号输入
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="border-2 border-dashed border-white/10 rounded-xl p-10 flex flex-col items-center justify-center text-zinc-500 hover:border-emerald-500/50 hover:bg-white/5 transition-all relative group">
                <Mic className="w-12 h-12 mb-4 text-zinc-600 group-hover:text-emerald-500 transition-colors" />
                <p className="mb-2 font-medium text-zinc-300 group-hover:text-white transition-colors">点击上传音频文件</p>
                <p className="text-xs">支持 .mp3, .wav 格式</p>
                
                {/* 隐藏的 input 覆盖在上面 */}
                <input 
                  type="file" 
                  accept=".mp3,.wav"
                  onChange={handleFileUpload}
                  className="absolute inset-0 opacity-0 cursor-pointer"
                  disabled={loading}
                />
              </div>

              {loading && (
                <div className="mt-6 space-y-2">
                  <div className="flex justify-between text-xs text-zinc-400">
                    <span>正在连接 Hugging Face...</span>
                    <span>处理中</span>
                  </div>
                  {/* 这里需要 Progress 组件，如果没装会报错，下面教你怎么装 */}
                  <div className="h-2 bg-zinc-800 rounded-full overflow-hidden">
                    <div className="h-full bg-emerald-500 animate-pulse w-2/3 shadow-[0_0_10px_rgba(16,185,129,0.5)]"></div>
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* 右侧：结果展示区 */}
          {result && (
            <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
              
              {/* 1. 核心结果：武器型号 */}
              <Card className="glass-card border-l-4 border-l-emerald-500">
                <CardContent className="p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <p className="text-sm text-zinc-500 font-mono mb-1">IDENTIFIED WEAPON</p>
                      <h2 className="text-4xl font-black text-white tracking-tight uppercase drop-shadow-lg">
                        {result.cloud.label}
                      </h2>
                    </div>
                    <div className="text-right">
                      <p className="text-sm text-zinc-500 font-mono mb-1">CONFIDENCE</p>
                      <div className="text-2xl font-bold text-emerald-400 drop-shadow-[0_0_10px_rgba(52,211,153,0.5)]">
                        {(result.cloud.confidence * 100).toFixed(1)}%
                      </div>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* 2. 本地计算结果：距离与方位 */}
              <div className="grid grid-cols-2 gap-4">
                <Card className="glass-card">
                  <CardContent className="p-6 flex flex-col items-center text-center">
                    <Target className="w-8 h-8 text-amber-500 mb-3 drop-shadow-lg" />
                    {/* 🛡️ 防御性代码：先判断是不是数字 */}
                    <div className="text-2xl font-bold text-zinc-100">
                      {typeof result.local.distance === 'number' 
                        ? result.local.distance.toFixed(1) 
                        : result.local.distance}
                      <span className="text-sm font-normal ml-1">m</span>
                    </div>
                    <p className="text-xs text-zinc-500 uppercase mt-1">Estimated Distance</p>
                  </CardContent>
                </Card>

                <Card className="glass-card">
                  <CardContent className="p-6 flex flex-col items-center text-center">
                    <Zap className="w-8 h-8 text-purple-500 mb-3 drop-shadow-lg" />
                    {/* 🛡️ 防御性代码：先判断是不是数字 */}
                    <div className="text-2xl font-bold text-zinc-100">
                      {typeof result.local.direction === 'number' 
                        ? result.local.direction.toFixed(1) 
                        : result.local.direction}
                      <span className="text-sm font-normal ml-1">°</span>
                    </div>
                    <p className="text-xs text-zinc-500 uppercase mt-1">Source Direction</p>
                  </CardContent>
                </Card>
              </div>

            </div>
          )}
        </div>
      </main>
    </div>
  );
}