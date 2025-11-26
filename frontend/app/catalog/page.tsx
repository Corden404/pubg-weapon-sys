"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge"; // 如果没安装 badge 可能会报错，可以先删掉 Badge 组件或者安装它
import { toast } from "sonner"; // 漂亮的提示
import { Search, Plus, Shield, Package, Activity, LogOut, Sword, Crosshair, Settings } from "lucide-react";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Label } from "@/components/ui/label";

interface Weapon {
  name: string;
  full_name: string;
  type: string;
  damage: number;
  image_url?: string;
}

export default function CatalogPage() {
  const router = useRouter();
  const [user, setUser] = useState("");
  const [weapons, setWeapons] = useState<Weapon[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({}); // 控制每个按钮的加载状态
  
  // 弹窗状态
  const [selectedWeapon, setSelectedWeapon] = useState<Weapon | null>(null);
  const [ammoCount, setAmmoCount] = useState(30);
  const [isDialogOpen, setIsDialogOpen] = useState(false);

  // 初始化
  useEffect(() => {
    const storedUser = localStorage.getItem("student_id");
    if (!storedUser) {
      router.push("/");
      return;
    }
    setUser(storedUser);

    // 获取武器列表
    fetch("/api/weapons")
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") setWeapons(data.weapons);
      });
  }, [router]);

  // 打开弹窗
  const openAddDialog = (weapon: Weapon) => {
    setSelectedWeapon(weapon);
    setAmmoCount(30); // 重置为默认值
    setIsDialogOpen(true);
  };

  // 确认添加
  const confirmAdd = async () => {
    if (!selectedWeapon) return;
    
    const weaponName = selectedWeapon.name;
    setLoading(prev => ({ ...prev, [weaponName]: true }));
    setIsDialogOpen(false); // 先关闭弹窗

    try {
      const res = await fetch("/api/inventory/add", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          student_id: user,
          weapon_name: weaponName,
          ammo_count: ammoCount
        })
      });
      
      if (res.ok) {
        toast.success(`已添加 ${weaponName} 到背包`, {
            description: `弹药 x${ammoCount} 已入库`
        });
      } else {
        toast.error("添加失败");
      }
    } catch (e) {
      toast.error("网络错误");
    } finally {
      setLoading(prev => ({ ...prev, [weaponName]: false }));
      setSelectedWeapon(null);
    }
  };

  // 过滤逻辑
  const filteredWeapons = weapons.filter(w => 
    w.name.toLowerCase().includes(search.toLowerCase()) || 
    w.full_name?.toLowerCase().includes(search.toLowerCase())
  );

  return (
    <div className="flex min-h-screen font-sans">
      
      {/* 侧边栏 (和 Dashboard 一样) */}
      <aside className="w-64 p-6 flex flex-col fixed h-full glass border-r border-white/5 z-50">
        <div className="flex items-center gap-3 mb-10 px-2">
            <div className="w-8 h-8 bg-gradient-to-br from-emerald-400 to-emerald-600 rounded-lg flex items-center justify-center shadow-lg shadow-emerald-500/20">
                <Shield className="text-white w-5 h-5" />
            </div>
            <span className="font-bold tracking-wider text-transparent bg-clip-text bg-gradient-to-r from-white to-white/60">武器管理系统</span>
        </div>
        <nav className="space-y-1 flex-1">
            <Button variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200" onClick={() => router.push('/dashboard')}>
                <Activity className="mr-2 h-4 w-4" /> 控制台
            </Button>
            <Button variant="ghost" className="w-full justify-start text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all duration-200">
                <Package className="mr-2 h-4 w-4" /> 武器库
            </Button>
            <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
                <Link href="/analyze">
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
      </aside>

      {/* 主内容区 */}
      <main className="flex-1 p-8 ml-64">
        <header className="mb-8 flex justify-between items-end">
          <div>
            <h1 className="text-3xl font-bold mb-2 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">武器图鉴</h1>
            <p className="text-zinc-400">浏览并申请战术装备</p>
          </div>
          
          {/* 搜索框 */}
          <div className="relative w-72">
            <Search className="absolute left-3 top-2.5 h-4 w-4 text-zinc-500" />
            <Input 
              placeholder="搜索型号 (AKM, M4...)" 
              className="pl-9 bg-black/20 border-white/10 focus-visible:ring-emerald-500/50 text-zinc-200 placeholder:text-zinc-600"
              value={search}
              onChange={e => setSearch(e.target.value)}
            />
          </div>
        </header>

        {/* 武器网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {filteredWeapons.map((w) => (
            <Card key={w.name} className="glass-card overflow-hidden group hover:border-emerald-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
              <div className="aspect-video bg-black/40 flex items-center justify-center p-4 relative">
                {/* 图片路径：自动去 public/images/ 找 */}
                <img 
                  src={`/images/${w.name}.png`} 
                  onError={(e) => e.currentTarget.src = "https://img.icons8.com/ios-filled/100/666666/gun.png"}
                  alt={w.name} 
                  className="h-32 object-contain drop-shadow-2xl group-hover:scale-105 transition-transform duration-300"
                />
                <div className="absolute top-3 right-3">
                   <span className="text-xs font-bold px-2 py-1 rounded bg-white/5 text-zinc-300 border border-white/10 backdrop-blur-md">
                     {w.type}
                   </span>
                </div>
              </div>
              
              <CardContent className="p-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-lg text-zinc-100">{w.full_name || w.name}</h3>
                    <p className="text-sm text-zinc-500">Base Damage: <span className="text-emerald-500">{w.damage}</span></p>
                  </div>
                </div>
                
                <Button 
                    className="w-full bg-white text-black hover:bg-zinc-200 font-bold shadow-lg shadow-white/10 transition-all hover:shadow-white/20"
                    onClick={() => openAddDialog(w)}
                    disabled={loading[w.name]}
                >
                    {loading[w.name] ? "Processing..." : (
                        <>
                            <Plus className="mr-2 h-4 w-4" /> 添加至背包
                        </>
                    )}
                </Button>
              </CardContent>
            </Card>
          ))}
        </div>

        {/* 弹窗组件 */}
        <Dialog open={isDialogOpen} onOpenChange={setIsDialogOpen}>
          <DialogContent className="glass border-white/10 text-zinc-100 sm:max-w-[425px]">
            <DialogHeader>
              <DialogTitle>配置装备: {selectedWeapon?.full_name}</DialogTitle>
              <DialogDescription className="text-zinc-400">
                请确认申请的弹药数量。
              </DialogDescription>
            </DialogHeader>
            <div className="grid gap-4 py-4">
              <div className="grid grid-cols-4 items-center gap-4">
                <Label htmlFor="ammo" className="text-right text-zinc-400">
                  弹药数
                </Label>
                <Input
                  id="ammo"
                  type="number"
                  value={ammoCount}
                  onChange={(e) => setAmmoCount(Number(e.target.value))}
                  className="col-span-3 bg-black/20 border-white/10 text-zinc-200 focus-visible:ring-emerald-500/50"
                  min={1}
                  max={999}
                />
              </div>
            </div>
            <DialogFooter>
              <Button 
                type="submit" 
                className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20"
                onClick={confirmAdd}
              >
                确认申请
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </main>
    </div>
  );
}