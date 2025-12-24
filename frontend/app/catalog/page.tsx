"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Card, CardContent } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { toast } from "sonner";
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
import WeaponImage from "@/components/WeaponImage";

interface Weapon {
  name: string;
  full_name: string;
  type: string;
  damage: number;
  image_url?: string;
  ammo_type?: string;
  stats?: {
    headshot_rate?: number;
    fire_rate?: number; // seconds per shot in DB seed
    range?: number;
    mag_size?: number;
    reload_time?: number;
  };
}

export default function CatalogPage() {
  const router = useRouter();
  const [user, setUser] = useState("");
  const [weapons, setWeapons] = useState<Weapon[]>([]);
  const [search, setSearch] = useState("");
  const [loading, setLoading] = useState<{ [key: string]: boolean }>({}); // 控制每个按钮的加载状态

  const [sortKey, setSortKey] = useState<
    "damage" | "rpm" | "range" | "reload_time" | "mag_size"
  >("damage");
  const [sortOrder, setSortOrder] = useState<"desc" | "asc">("desc");

  const parseSortKey = (value: string) => {
    const allowed = ["damage", "rpm", "range", "reload_time", "mag_size"] as const;
    if ((allowed as readonly string[]).includes(value)) {
      return value as (typeof allowed)[number];
    }
    return "damage";
  };
  
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

  const getSortValue = (w: Weapon) => {
    if (sortKey === "damage") return Number.isFinite(w.damage) ? w.damage : 0;
    if (sortKey === "range") return Number(w.stats?.range ?? 0);
    if (sortKey === "reload_time") return Number(w.stats?.reload_time ?? 0);
    if (sortKey === "mag_size") return Number(w.stats?.mag_size ?? 0);
    // rpm
    // 注意：DB 里 fire_rate 的含义是「每发间隔（秒）」而不是 RPM。
    const fireInterval = Number(w.stats?.fire_rate ?? 0);
    if (!fireInterval || fireInterval <= 0) return 0;
    return 60 / fireInterval;
  };

  const formatNumber = (value: unknown, digits = 0) => {
    const n = typeof value === "number" ? value : Number(value);
    if (!Number.isFinite(n)) return "—";
    return n.toFixed(digits);
  };

  const getRpm = (w: Weapon) => {
    const fireInterval = Number(w.stats?.fire_rate ?? 0);
    if (!fireInterval || fireInterval <= 0) return null;
    return 60 / fireInterval;
  };

  const sortedWeapons = [...filteredWeapons].sort((a, b) => {
    const av = getSortValue(a);
    const bv = getSortValue(b);
    if (sortOrder === "asc") return av - bv;
    return bv - av;
  });

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
          
          <div className="flex items-end gap-3">
            {/* 排序 */}
            <div className="flex flex-col gap-1">
              <span className="text-xs text-zinc-500">排序</span>
              <div className="flex gap-2">
                <select
                  value={sortKey}
                  onChange={(e) => setSortKey(parseSortKey(e.target.value))}
                  className="h-10 rounded-md bg-black/20 border border-white/10 px-3 text-sm text-zinc-200 focus:outline-none focus:ring-2 focus:ring-emerald-500/50"
                >
                  <option value="damage">伤害</option>
                  <option value="rpm">射速 (RPM)</option>
                  <option value="range">射程</option>
                  <option value="mag_size">弹匣</option>
                  <option value="reload_time">装填时间</option>
                </select>
                <Button
                  variant="outline"
                  className="border-white/10 bg-white/5 hover:bg-white/10 text-zinc-300"
                  onClick={() => setSortOrder((p) => (p === "desc" ? "asc" : "desc"))}
                >
                  {sortOrder === "desc" ? "降序" : "升序"}
                </Button>
              </div>
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
          </div>
        </header>

        {/* 武器网格 */}
        <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
          {sortedWeapons.map((w) => (
            <Card key={w.name} className="glass-card overflow-hidden group hover:border-emerald-500/30 transition-all duration-300 hover:shadow-lg hover:shadow-emerald-500/10">
              {/* 图片展示区 */}
              <div className="aspect-video bg-zinc-950/50 flex items-center justify-center p-6 relative group-hover:bg-zinc-900/50 transition-colors border-b border-zinc-800/50">
                {/* 调用智能组件 */}
                <WeaponImage 
                  name={w.name} 
                  alt={w.full_name} 
                  className="w-full h-full z-10" // 确保图片填满容器
                />

                {/* 背景装饰光晕 (让图片看起来更高级) */}
                <div className="absolute inset-0 bg-gradient-to-t from-zinc-900/80 to-transparent z-0 pointer-events-none"></div>

                {/* 右上角标签 (保持不变) */}
                <div className="absolute top-3 right-3 z-20">
                   <span className="text-[10px] font-bold px-2 py-1 rounded bg-zinc-900/80 text-zinc-400 border border-zinc-700 backdrop-blur-sm uppercase tracking-wider">
                     {w.type}
                   </span>
                </div>
              </div>
              
              <CardContent className="p-5">
                <div className="flex justify-between items-start mb-4">
                  <div>
                    <h3 className="font-bold text-lg text-zinc-100">{w.full_name || w.name}</h3>
                    <p className="text-xs text-zinc-500 mt-0.5">型号: <span className="text-zinc-300 font-mono">{w.name}</span></p>

                    {/* 属性面板 */}
                    <div className="mt-3 grid grid-cols-2 gap-x-4 gap-y-1.5 text-xs">
                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">伤害</span>
                        <span className="text-emerald-500 font-mono font-bold">{formatNumber(w.damage, 0)}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">弹药</span>
                        <span className="text-zinc-200 font-mono">{w.ammo_type || "—"}</span>
                      </div>

                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">射速(RPM)</span>
                        <span className="text-zinc-200 font-mono">
                          {(() => {
                            const rpm = getRpm(w);
                            return rpm ? Math.round(rpm).toString() : "—";
                          })()}
                        </span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">射程</span>
                        <span className="text-zinc-200 font-mono">{formatNumber(w.stats?.range, 0)}</span>
                      </div>

                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">弹匣</span>
                        <span className="text-zinc-200 font-mono">{formatNumber(w.stats?.mag_size, 0)}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">装填(s)</span>
                        <span className="text-zinc-200 font-mono">{formatNumber(w.stats?.reload_time, 1)}</span>
                      </div>

                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">爆头倍率</span>
                        <span className="text-zinc-200 font-mono">{formatNumber(w.stats?.headshot_rate, 1)}</span>
                      </div>
                      <div className="flex justify-between gap-2">
                        <span className="text-zinc-500">类型</span>
                        <span className="text-zinc-200">{w.type || "—"}</span>
                      </div>
                    </div>
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