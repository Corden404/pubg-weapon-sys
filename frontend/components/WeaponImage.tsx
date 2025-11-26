"use client";

import { useState, useEffect } from "react";
import Image from "next/image"; // 使用 Next.js 自带的 Image 组件优化性能
import { Crosshair } from "lucide-react"; // 用于图片完全加载失败时的最终兜底

interface WeaponImageProps {
  name: string;      // 武器名称 (数据库里的 name)
  alt: string;       // 图片描述
  className?: string; // 允许外部传入样式
}

export default function WeaponImage({ name, alt, className }: WeaponImageProps) {
  // 1. 默认先猜它是 .webp
  const [src, setSrc] = useState(`/images/${name}.webp`);
  const [attempt, setAttempt] = useState(0); // 记录重试次数

  // 当 name 变化时，重置状态
  useEffect(() => {
    setSrc(`/images/${name}.webp`);
    setAttempt(0);
  }, [name]);

  const handleError = () => {
    if (attempt === 0) {
      // 第一次失败：可能是 .png，尝试切换后缀
      setSrc(`/images/${name}.png`);
      setAttempt(1);
    } else if (attempt === 1) {
      // 第二次失败：说明既不是 webp 也不是 png，加载默认图
      setSrc("/images/ak.webp");
      setAttempt(2);
    }
    // 如果 attempt === 2 还是失败（连 ak.webp 都没有），Next.js Image 会显示裂图，或者我们可以不管了
  };

  return (
    <div className={`relative flex items-center justify-center overflow-hidden ${className}`}>
      {/* 
        使用标准 img 标签而不是 next/image 的 fill 模式，
        因为在这个场景下我们需要频繁处理 onError，原生 img 更可控。
        如果你想用 next/image，需要配置 width/height。
      */}
      <img
        src={src}
        alt={alt}
        onError={handleError}
        className="object-contain w-full h-full drop-shadow-2xl transition-transform duration-300 hover:scale-110"
      />
    </div>
  );
}