"use client"; // 👈 必须加这行，因为我们要用 useState (交互)

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Loader2, ShieldAlert, Terminal } from "lucide-react"; // 图标
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); // 阻止表单默认刷新
    setLoading(true);
    setError("");

    try {
      // 1. 调用 FastAPI 后端
      // 注意：Codespaces 的后端地址通常是 localhost:8000
      // 如果你在 Codespaces 浏览器预览，可能需要用相对路径或配置代理，
      // 但为了简单，我们先假设本地联调。
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, password: password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "登录失败");
      }

      // 2. 登录成功
      // 1. 保存学号到 localStorage (简单起见)
      localStorage.setItem("student_id", data.user.student_id);

      // 2. 跳转
      router.push("/dashboard");

    } catch (err: any) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    // --- 全局背景：由 globals.css 控制，这里只需居中 ---
    <div className="min-h-screen flex items-center justify-center p-4">
      
      {/* --- 登录卡片：Glass 风格 --- */}
      <Card className="w-full max-w-md glass border-0 text-zinc-100">
        <CardHeader className="space-y-1">
          <div className="flex items-center gap-2 mb-2">
            <div className="p-2 bg-white/5 rounded-lg border border-white/10">
              <Terminal className="w-6 h-6 text-emerald-400" />
            </div>
            <span className="text-sm font-mono text-zinc-400">PUBG_SYS_V2.0</span>
          </div>
          <CardTitle className="text-2xl font-bold tracking-tight text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">
            指挥官登录
          </CardTitle>
          <CardDescription className="text-zinc-400">
            请输入您的学号与安全密钥以访问武器库
          </CardDescription>
        </CardHeader>
        
        <form onSubmit={handleLogin}>
          <CardContent className="space-y-4">
            {/* 错误提示条 */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-md flex items-center gap-2 text-sm text-red-400">
                <ShieldAlert className="w-4 h-4" />
                {error}
              </div>
            )}

            <div className="space-y-2">
              <Label htmlFor="sid" className="text-zinc-300">学号 (Student ID)</Label>
              <Input 
                id="sid" 
                placeholder="2021xxxx" 
                className="bg-black/20 border-white/10 focus-visible:ring-emerald-500/50 placeholder:text-zinc-600 text-zinc-200"
                value={studentId}
                onChange={(e) => setStudentId(e.target.value)}
                required
              />
            </div>
            <div className="space-y-2">
              <Label htmlFor="pwd" className="text-zinc-300">密码 (Password)</Label>
              <Input 
                id="pwd" 
                type="password" 
                className="bg-black/20 border-white/10 focus-visible:ring-emerald-500/50 text-zinc-200"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>
          </CardContent>
          
          <CardFooter>
            <Button 
              type="submit" 
              className="w-full bg-emerald-600/80 hover:bg-emerald-600 text-white font-medium border border-emerald-500/50 shadow-[0_0_20px_rgba(16,185,129,0.3)] transition-all hover:shadow-[0_0_30px_rgba(16,185,129,0.5)]"
              disabled={loading}
            >
              {loading ? (
                <>
                  <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                  验证中...
                </>
              ) : (
                "进入系统"
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}