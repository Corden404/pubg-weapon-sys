"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import Link from "next/link";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Shield, Activity, Package, Sword, Settings, Lock, Pencil } from "lucide-react";
import { toast } from "sonner";

interface Weapon {
  name: string;
  full_name: string;
  type: string;
  damage: number;
}

interface InventoryItem {
  weapon_name: string;
  ammo_count: number;
  added_at?: string;
  weapon?: Weapon & {
    ammo_type?: string;
    stats?: {
      fire_rate?: number;
      range?: number;
      mag_size?: number;
      reload_time?: number;
    };
  };
}

interface UserInventory {
  student_id: string;
  role: string;
  inventory_count: number;
  inventory: InventoryItem[];
}

export default function AdminPage() {
  const router = useRouter();
  const [weapons, setWeapons] = useState<Weapon[]>([]);
  const [loading, setLoading] = useState(true);

  const [users, setUsers] = useState<UserInventory[]>([]);
  const [usersLoading, setUsersLoading] = useState(true);
  
  // 编辑状态
  const [editingWeapon, setEditingWeapon] = useState<Weapon | null>(null);
  const [newDamage, setNewDamage] = useState(0);
  const [newType, setNewType] = useState("");
  const [isSaving, setIsSaving] = useState(false);

  useEffect(() => {
    const user = localStorage.getItem("student_id");
    const role = localStorage.getItem("role");
    if (!user) {
      router.push("/");
      return;
    }

    // 这里的 role 判断主要是“用户体验层”的拦截（避免普通用户看到管理页）。
    // 真正的权限控制在后端：管理员接口会校验 X-Student-Id 对应用户的 role。
    if (role !== "admin") {
      router.push("/dashboard");
      return;
    }
    
    // 2. 获取数据
    fetchWeapons();
    fetchUsersWeapons(user);
  }, [router]);

  const fetchWeapons = () => {
    fetch("/api/weapons")
      .then(res => res.json())
      .then(data => {
        setWeapons(data.weapons);
        setLoading(false);
      });
  };

  const fetchUsersWeapons = (studentId: string) => {
    setUsersLoading(true);
    fetch("/api/admin/users/weapons", {
      headers: {
        // 该 header 用于后端鉴权 & 审计日志；并不等价于安全登录态。
        "X-Student-Id": studentId,
      }
    })
      .then(res => res.json())
      .then(data => {
        if (data.status === "success") {
          setUsers(data.users || []);
        }
      })
      .finally(() => setUsersLoading(false));
  };

  // 打开编辑弹窗
  const openEdit = (w: Weapon) => {
    setEditingWeapon(w);
    setNewDamage(w.damage);
    setNewType(w.type);
  };

  // 保存修改
  const handleSave = async () => {
    if (!editingWeapon) return;
    setIsSaving(true);

    try {
      const res = await fetch(`/api/weapons/${editingWeapon.name}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          damage: newDamage,
          type: newType
        })
      });

      if (res.ok) {
        toast.success("数据库已更新", { description: `${editingWeapon.name} 属性已修改` });
        setEditingWeapon(null); // 关闭弹窗
        fetchWeapons(); // 刷新列表
      } else {
        toast.error("更新失败");
      }
    } catch (e) {
      toast.error("网络错误");
    } finally {
      setIsSaving(false);
    }
  };

  return (
    <div className="flex min-h-screen font-sans">
      
      {/* 侧边栏 */}
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
            <Button asChild variant="ghost" className="w-full justify-start text-zinc-400 hover:text-zinc-100 hover:bg-white/5 transition-all duration-200">
                <Link href="/analyze"><Sword className="mr-2 h-4 w-4" /> AI 识别</Link>
            </Button>
            {/* 管理员高亮 */}
            <Button asChild variant="ghost" className="w-full justify-start text-emerald-400 bg-emerald-500/10 hover:bg-emerald-500/20 hover:text-emerald-300 transition-all duration-200">
                <Link href="/admin"><Settings className="mr-2 h-4 w-4" /> 系统管理</Link>
            </Button>
        </nav>
      </aside>

      {/* 主内容 */}
      <main className="flex-1 p-8 ml-64">
        <header className="mb-8 flex items-center gap-4">
          <div className="p-3 bg-red-500/10 rounded-xl border border-red-500/20 shadow-[0_0_15px_rgba(239,68,68,0.2)]">
            <Lock className="w-6 h-6 text-red-500" />
          </div>
          <div>
            <h1 className="text-3xl font-bold mb-1 text-transparent bg-clip-text bg-gradient-to-b from-white to-white/60">系统底层管理</h1>
            <p className="text-zinc-400">修改全局武器参数（慎用）</p>
          </div>
        </header>

        <div className="glass-card rounded-xl overflow-hidden">
          <Table>
            <TableHeader className="bg-white/5">
              <TableRow className="border-white/5 hover:bg-white/5">
                <TableHead className="text-zinc-400">Weapon Name</TableHead>
                <TableHead className="text-zinc-400">Type</TableHead>
                <TableHead className="text-zinc-400">Base Damage</TableHead>
                <TableHead className="text-right text-zinc-400">Action</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {weapons.map((w) => (
                <TableRow key={w.name} className="border-white/5 hover:bg-white/5 transition-colors">
                  <TableCell className="font-medium text-zinc-200">
                    {w.full_name || w.name}
                    <span className="ml-2 text-xs text-zinc-500 font-mono">({w.name})</span>
                  </TableCell>
                  <TableCell>
                    <span className="px-2 py-1 rounded bg-white/5 text-xs text-zinc-300 border border-white/10">
                        {w.type}
                    </span>
                  </TableCell>
                  <TableCell className="text-emerald-500 font-mono font-bold">
                    {w.damage}
                  </TableCell>
                  <TableCell className="text-right">
                    <Dialog open={editingWeapon?.name === w.name} onOpenChange={(open: boolean) => !open && setEditingWeapon(null)}>
                      <DialogTrigger asChild>
                        <Button 
                            variant="outline" 
                            size="sm" 
                            className="border-white/10 bg-white/5 hover:bg-white/10 text-zinc-400 hover:text-white transition-all"
                            onClick={() => openEdit(w)}
                        >
                          <Pencil className="w-3 h-3 mr-2" /> Edit
                        </Button>
                      </DialogTrigger>
                      
                      {/* 编辑弹窗 */}
                      <DialogContent className="glass border-white/10 text-zinc-100 sm:max-w-[425px]">
                        <DialogHeader>
                          <DialogTitle>编辑参数: {w.full_name}</DialogTitle>
                          <DialogDescription className="text-zinc-400">
                            修改将实时同步至所有终端。
                          </DialogDescription>
                        </DialogHeader>
                        <div className="grid gap-4 py-4">
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="dmg" className="text-right text-zinc-400">Damage</Label>
                            <Input 
                                id="dmg" 
                                type="number" 
                                value={newDamage} 
                                onChange={(e) => setNewDamage(Number(e.target.value))}
                                className="col-span-3 bg-black/20 border-white/10 text-zinc-200 focus-visible:ring-emerald-500/50" 
                            />
                          </div>
                          <div className="grid grid-cols-4 items-center gap-4">
                            <Label htmlFor="type" className="text-right text-zinc-400">Type</Label>
                            <Input 
                                id="type" 
                                value={newType} 
                                onChange={(e) => setNewType(e.target.value)}
                                className="col-span-3 bg-black/20 border-white/10 text-zinc-200 focus-visible:ring-emerald-500/50" 
                            />
                          </div>
                        </div>
                        <DialogFooter>
                          <Button 
                            type="submit" 
                            className="bg-emerald-600 hover:bg-emerald-700 text-white shadow-lg shadow-emerald-500/20"
                            onClick={handleSave}
                            disabled={isSaving}
                          >
                            {isSaving ? "Saving..." : "Save Changes"}
                          </Button>
                        </DialogFooter>
                      </DialogContent>
                    </Dialog>
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>

        <div className="h-8" />

        <header className="mb-4">
          <h2 className="text-xl font-bold text-zinc-100">玩家武器详情</h2>
          <p className="text-zinc-400 text-sm">查看所有玩家背包明细（管理员）</p>
        </header>

        <div className="glass-card rounded-xl overflow-hidden">
          <Table>
            <TableHeader className="bg-white/5">
              <TableRow className="border-white/5 hover:bg-white/5">
                <TableHead className="text-zinc-400">Student ID</TableHead>
                <TableHead className="text-zinc-400">Role</TableHead>
                <TableHead className="text-zinc-400">Items</TableHead>
                <TableHead className="text-zinc-400">Weapons</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              {usersLoading ? (
                <TableRow className="border-white/5">
                  <TableCell className="text-zinc-500" colSpan={4}>Loading...</TableCell>
                </TableRow>
              ) : users.length === 0 ? (
                <TableRow className="border-white/5">
                  <TableCell className="text-zinc-500" colSpan={4}>暂无数据</TableCell>
                </TableRow>
              ) : users.map((u) => (
                <TableRow key={u.student_id} className="border-white/5 hover:bg-white/5 transition-colors align-top">
                  <TableCell className="font-medium text-zinc-200">{u.student_id}</TableCell>
                  <TableCell>
                    <span className="px-2 py-1 rounded bg-white/5 text-xs text-zinc-300 border border-white/10">
                      {u.role}
                    </span>
                  </TableCell>
                  <TableCell className="text-zinc-300 font-mono">{u.inventory_count}</TableCell>
                  <TableCell className="text-zinc-300">
                    {u.inventory_count === 0 ? (
                      <span className="text-zinc-500">(empty)</span>
                    ) : (
                      <div className="space-y-1">
                        {u.inventory.slice(0, 6).map((it, idx) => (
                          <div key={idx} className="text-sm">
                            <span className="text-zinc-200">{it.weapon?.full_name || it.weapon_name}</span>
                            <span className="text-zinc-500"> · ammo {it.ammo_count}</span>
                            {typeof it.weapon?.damage === "number" && (
                              <span className="text-zinc-500"> · dmg {it.weapon.damage}</span>
                            )}
                            {typeof it.weapon?.stats?.fire_rate === "number" && it.weapon.stats.fire_rate > 0 && (
                              <span className="text-zinc-500"> · rpm {Math.round(60 / it.weapon.stats.fire_rate)}</span>
                            )}
                          </div>
                        ))}
                        {u.inventory.length > 6 && (
                          <div className="text-xs text-zinc-500">... +{u.inventory.length - 6} more</div>
                        )}
                      </div>
                    )}
                  </TableCell>
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </main>
    </div>
  );
}