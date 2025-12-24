"use client";

import { useEffect, useRef } from "react";

interface WeaponImageProps {
  name: string; // 武器唯一名（与 public/images 下的文件名一致）
  alt: string;
  className?: string;
}

export default function WeaponImage({ name, alt, className }: WeaponImageProps) {
  const attemptRef = useRef(0);

  useEffect(() => {
    attemptRef.current = 0;
  }, [name]);

  const handleError = (e: React.SyntheticEvent<HTMLImageElement>) => {
    const img = e.currentTarget;
    if (attemptRef.current === 0) {
      // 第一次失败：可能是 .png，尝试切换后缀
      attemptRef.current = 1;
      img.src = `/images/${name}.png`;
      return;
    }
    if (attemptRef.current === 1) {
      // 第二次失败：说明既不是 webp 也不是 png，加载默认图
      attemptRef.current = 2;
      img.src = "/images/ak.webp";
    }
  };

  return (
    <div className={`relative flex items-center justify-center overflow-hidden ${className}`}>
      {/* 
        这里用原生 img：
        - onError 回退链（webp -> png -> default）更好控制
        - 静态图片不需要 next/image 的优化收益
      */}
      <img
        key={name}
        src={`/images/${name}.webp`}
        alt={alt}
        onError={handleError}
        className="object-contain w-full h-full drop-shadow-2xl transition-transform duration-300 hover:scale-110"
      />
    </div>
  );
}