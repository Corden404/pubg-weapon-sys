"use client"; // Client Component：页面里用到了 hooks。

import { useState } from "react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Card, CardContent, CardDescription, CardHeader, CardTitle, CardFooter } from "@/components/ui/card";
import { Label } from "@/components/ui/label";
import { Loader2, ShieldAlert, Terminal } from "lucide-react"; // 图标
import { useRouter } from "next/navigation";

export default function LoginPage() {
  const [loading, setLoading] = useState(false);
  const [mode, setMode] = useState<"login" | "register">("login");
  const [studentId, setStudentId] = useState("");
  const [password, setPassword] = useState("");
  const [confirmPassword, setConfirmPassword] = useState("");
  const [error, setError] = useState("");
  const [success, setSuccess] = useState("");
  const router = useRouter();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault(); // 阻止表单默认刷新
    setLoading(true);
    setError("");
    setSuccess("");

    try {
      // 通过 Next.js 的 /api 反向代理访问 FastAPI。
      // 具体代理规则在 next.config.ts 的 rewrites 里配置。
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: studentId, password: password }),
      });

      const data = await res.json();

      if (!res.ok) {
        throw new Error(data.detail || "登录失败");
      }

      // 登录态这里用 localStorage 做“演示级”的持久化。
      // 这不是安全方案：权限/鉴权以服务端校验为准（尤其是管理员接口）。
      localStorage.setItem("student_id", data.user.student_id);
      if (data?.user?.role) {
        localStorage.setItem("role", data.user.role);
      }
      if (typeof data?.user?.is_admin === "boolean") {
        localStorage.setItem("is_admin", String(data.user.is_admin));
      }

      // 2. 跳转
      router.push("/dashboard");

    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("登录失败");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    setSuccess("");

    const sid = studentId.trim();
    if (!sid) {
      setError("学号不能为空");
      setLoading(false);
      return;
    }
    if (password.length < 3) {
      setError("密码长度太短");
      setLoading(false);
      return;
    }
    if (password !== confirmPassword) {
      setError("两次密码输入不一致");
      setLoading(false);
      return;
    }

    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ student_id: sid, password }),
      });

      const data = await res.json();
      if (!res.ok) {
        throw new Error(data.detail || "注册失败");
      }

      setSuccess("注册成功，请登录");
      setMode("login");
      setPassword("");
      setConfirmPassword("");
    } catch (err: unknown) {
      if (err instanceof Error) setError(err.message);
      else setError("注册失败");
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
            {mode === "login" ? "指挥官登录" : "注册新账号"}
          </CardTitle>
          <CardDescription className="text-zinc-400">
            {mode === "login"
              ? "请输入您的学号与安全密钥以访问武器库"
              : "创建账号后即可登录进入系统"}
          </CardDescription>

          <div className="pt-2 flex gap-2">
            <Button
              type="button"
              variant="ghost"
              className={
                mode === "login"
                  ? "text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }
              onClick={() => {
                setMode("login");
                setError("");
                setSuccess("");
              }}
              disabled={loading}
            >
              登录
            </Button>
            <Button
              type="button"
              variant="ghost"
              className={
                mode === "register"
                  ? "text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20"
                  : "text-zinc-400 hover:text-zinc-200 hover:bg-white/5"
              }
              onClick={() => {
                setMode("register");
                setError("");
                setSuccess("");
              }}
              disabled={loading}
            >
              注册
            </Button>
          </div>
        </CardHeader>

        <form onSubmit={mode === "login" ? handleLogin : handleRegister}>
          <CardContent className="space-y-4">
            {/* 错误提示条 */}
            {error && (
              <div className="bg-red-500/10 border border-red-500/20 p-3 rounded-md flex items-center gap-2 text-sm text-red-400">
                <ShieldAlert className="w-4 h-4" />
                {error}
              </div>
            )}

            {success && (
              <div className="bg-emerald-500/10 border border-emerald-500/20 p-3 rounded-md flex items-center gap-2 text-sm text-emerald-300">
                {success}
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

            {mode === "register" && (
              <div className="space-y-2">
                <Label htmlFor="pwd2" className="text-zinc-300">确认密码</Label>
                <Input
                  id="pwd2"
                  type="password"
                  className="bg-black/20 border-white/10 focus-visible:ring-emerald-500/50 text-zinc-200"
                  value={confirmPassword}
                  onChange={(e) => setConfirmPassword(e.target.value)}
                  required
                />
              </div>
            )}
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
                  {mode === "login" ? "验证中..." : "注册中..."}
                </>
              ) : (
                mode === "login" ? "进入系统" : "创建账号"
              )}
            </Button>
          </CardFooter>
        </form>
      </Card>
    </div>
  );
}