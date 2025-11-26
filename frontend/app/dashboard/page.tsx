"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation"; // 路由跳转
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer } from 'recharts';
import { Package, Shield, Activity, LogOut, Sword, Zap, Settings } from "lucide-react";
import Link from "next/link";

// 定义数据类型
interface InventoryItem {
  weapon_name: string;
  ammo_count: number;
  added_at: string;
}

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState("Unknown");
  const [items, setItems] = useState<InventoryItem[]>([]);
  const [stats, setStats] = useState({ total_ammo: 0, total_weapons: 0, recent_item: "None" });

  useEffect(() => {
    // 1. 从 localStorage 获取登录态 (简化版，实际项目用 Context)
    const storedUser = localStorage.getItem("student_id");
    if (!storedUser) {
      router.push("/"); // 没登录就踢回首页
      return;
    }
    setUser(storedUser);

    // 2. 获取数据
    fetch(`/api/inventory/${storedUser}`)
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setItems(data.inventory);
          setStats(data.stats);
        }
      });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("student_id");
    router.push("/");
  };

  return (
    <div className="flex min-h-screen font-sans">
      
      {/* --- 左侧侧边栏 (Sidebar) --- */}
      <aside className="w-64 p-6 flex flex-col fixed h-full glass border-r border-white/5 z-50">
        <div className="flex items-center gap-3 mb-10 px-2">
          <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
            <Shield className="text-white w-5 h-5" />
          </div>
          <span className="font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">武器管理系统</span>
        </div>

<nav className="space-y-1 flex-1">
  {/* 1. 控制台 (当前页 - 高亮显示) */}
  <Button asChild variant="ghost" className="w-full justify-start text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all duration-200">
    <Link href="/dashboard">
      <Activity className="mr-2 h-4 w-4" />
      控制台
    </Link>
  </Button>

  {/* 2. 武器库 (跳转目标) */}
  <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
    <Link href="/catalog">
      <Package className="mr-2 h-4 w-4" />
      武器库
    </Link>
  </Button>

  {/* 3. AI 识别 (预留) */}
  <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
    <Link href="#">
      <Sword className="mr-2 h-4 w-4" />
      AI 识别
    </Link>
  </Button>
  <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
      <Link href="/admin">
          <Settings className="mr-2 h-4 w-4" />
          系统管理
      </Link>
  </Button>
</nav>

        <div className="pt-6 border-t border-white/5">
          <div className="flex items-center gap-3 mb-4 px-2">
            <div className="w-8 h-8 rounded-full bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center text-xs font-bold shadow-lg">
              {user.slice(0, 2).toUpperCase()}
            </div>
            <div className="text-sm">
              <div className="font-medium text-zinc-200">{user}</div>
              <div className="text-xs text-zinc-500">指挥官</div>
            </div>
          </div>
          <Button variant="outline" className="w-full border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-zinc-200 transition-all" onClick={handleLogout}>
            <LogOut className="mr-2 h-4 w-4" /> 退出系统
          </Button>
        </div>
      </aside>

      {/* --- 右侧主内容 --- */}
      <main className="flex-1 p-8 ml-64 overflow-y-auto">
        <header className="mb-8">
          <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">指挥中心概览</h1>
          <p className="text-zinc-400">系统运行正常，数据实时同步中...</p>
        </header>

        {/* 顶部指标卡片 */}
        <div className="grid gap-4 md:grid-cols-3 mb-8">
          <Card className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">总弹药储备</CardTitle>
              <Zap className="h-4 w-4 text-emerald-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stats.total_ammo}</div>
              <p className="text-xs text-emerald-500 mt-1">+12% 较上周</p>
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">现役武器数</CardTitle>
              <Sword className="h-4 w-4 text-blue-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stats.total_weapons}</div>
              <p className="text-xs text-zinc-500 mt-1">库存充足</p>
            </CardContent>
          </Card>
          <Card className="glass-card">
            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
              <CardTitle className="text-sm font-medium text-zinc-400">最新入库</CardTitle>
              <Package className="h-4 w-4 text-amber-500" />
            </CardHeader>
            <CardContent>
              <div className="text-2xl font-bold text-white">{stats.recent_item}</div>
              <p className="text-xs text-zinc-500 mt-1">刚刚更新</p>
            </CardContent>
          </Card>
        </div>

        {/* 中间图表区 + 列表区 */}
        <div className="grid gap-4 md:grid-cols-7">
          
          {/* 左侧图表 (占4列) */}
          <Card className="col-span-4 glass-card">
            <CardHeader>
              <CardTitle className="text-zinc-200">弹药分布趋势</CardTitle>
            </CardHeader>
            <CardContent className="pl-2">
              <div className="h-[300px]">
                <ResponsiveContainer width="100%" height="100%">
                  <AreaChart data={items}>
                    <defs>
                      <linearGradient id="colorAmmo" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#10b981" stopOpacity={0.3}/>
                        <stop offset="95%" stopColor="#10b981" stopOpacity={0}/>
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.1)" vertical={false} />
                    <XAxis dataKey="weapon_name" stroke="#666" tickLine={false} axisLine={false} />
                    <YAxis stroke="#666" tickLine={false} axisLine={false} />
                    <Tooltip 
                      contentStyle={{
                        backgroundColor: 'rgba(0, 0, 0, 0.8)', 
                        backdropFilter: 'blur(12px)',            
                        border: '1px solid rgba(255,255,255,0.1)', 
                        borderRadius: '8px',
                        boxShadow: '0 4px 20px rgba(0,0,0,0.5)'
                      }} 
                      itemStyle={{color: '#fff'}}
                    />
                    <Area type="monotone" dataKey="ammo_count" stroke="#10b981" fillOpacity={1} fill="url(#colorAmmo)" />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            </CardContent>
          </Card>

          {/* 右侧列表 (占3列) */}
          <Card className="col-span-3 glass-card">
            <CardHeader>
              <CardTitle className="text-zinc-200">背包明细</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                {items.length === 0 ? (
                  <p className="text-zinc-500 text-sm">暂无数据</p>
                ) : items.map((item, i) => (
                  <div key={i} className="flex items-center group">
                    <div className="h-9 w-9 rounded-full bg-white/5 flex items-center justify-center border border-white/10 group-hover:border-emerald-500/50 transition-colors">
                      <span className="text-xs font-bold text-zinc-300 group-hover:text-emerald-400">W</span>
                    </div>
                    <div className="ml-4 space-y-1">
                      <p className="text-sm font-medium leading-none text-zinc-200 group-hover:text-white transition-colors">{item.weapon_name}</p>
                      <p className="text-xs text-zinc-500">库存</p>
                    </div>
                    <div className="ml-auto font-medium text-emerald-500">+{item.ammo_count}</div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      </main>
    </div>
  );
}