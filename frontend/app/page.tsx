"use client";

import Link from "next/link";
import Image from "next/image";

const assignments = [
  {
    id: "odev1",
    href: "/odev1",
    title: "Model Karşılaştırması — PPE",
    subtitle: "1. Ödev",
    description:
      "Kişisel Koruyucu Ekipman (PPE) tespiti için YOLO model karşılaştırması. PDF rapor yükleyin ve best.pt modelinizi test edin.",
    icon: "🛡️",
    gradient: "from-[#6c63ff] to-[#4834d4]",
    tags: ["Object Detection", "PPE", "YOLO"],
  },
  {
    id: "odev2",
    href: "/odev2",
    title: "Instance Segmentation — Car Damage",
    subtitle: "2. Ödev",
    description:
      "YOLO11l ve RF-DETR model karşılaştırması ile araç hasar tespiti. Segmentasyon modelinizi yükleyip test edin.",
    icon: "🚗",
    gradient: "from-[#00d2ff] to-[#3a7bd5]",
    tags: ["Segmentation", "YOLO11l", "RF-DETR"],
  },
  {
    id: "peoplecounter",
    href: "/peoplecounter",
    title: "YOLO26 İnsan Sayma",
    subtitle: "People Counter",
    description:
      "YOLO26 modeli ile gerçek zamanlı webcam üzerinden insan tespiti ve sayımı. Canlı video stream ile izleyin.",
    icon: "👥",
    gradient: "from-[#00ffc8] to-[#00b894]",
    tags: ["YOLO26", "Real-time", "Webcam"],
  },
];

export default function DashboardPage() {
  return (
    <div className="page-enter max-w-6xl mx-auto px-4 md:px-6 py-8 md:py-12">
      {/* Hero Text */}
      <div className="text-center mb-10">
        <h1 className="text-4xl md:text-5xl lg:text-6xl font-black mb-4 leading-tight">
          <span className="gradient-text">Makine Öğrenmesi <br className="hidden md:block" /> Yapay Sinir Ağları ve <br className="hidden md:block" /> Derin Öğrenme Projesi</span>
        </h1>

        <p className="text-[#a0a0b5] text-lg max-w-2xl mx-auto">
          Yapay Sinir Ağları ve Derin Öğrenme dersi proje ve ödevleri. YOLO tabanlı nesne tespiti,
          segmentasyon ve gerçek zamanlı insan sayma
        </p>

        {/* Projeyi Yapanlar */}
        <p className="text-sm text-gray-400 font-medium mt-4">
          Bu ödev, Yasin KARAÇAM, Mustafa Atacan AKDEMİR ve Mübarek Yasin tarafından yapılmıştır.
        </p>
      </div>

      {/* Hero Image */}
      <div className="relative w-full max-w-5xl mx-auto mb-16 rounded-3xl overflow-hidden glass-card p-2 border border-white/10 shadow-[0_0_50px_rgba(108,99,255,0.15)]">
        <div className="relative aspect-[21/9] w-full rounded-2xl overflow-hidden">
          <Image
            src="/hero.png"
            alt="ML Dashboard Hero"
            fill
            className="object-cover"
            priority
          />
          {/* Overlay Gradient */}
          <div className="absolute inset-0 bg-gradient-to-t from-[#0f0f13] via-transparent to-transparent opacity-80" />
        </div>
      </div>

      {/* Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {assignments.map((item) => (
          <Link key={item.id} href={item.href} className="block group">
            <div className="glass-card gradient-border p-6 h-full flex flex-col">
              {/* Icon & Badge */}
              <div className="flex items-center justify-between mb-4">
                <div
                  className={`w-14 h-14 rounded-2xl bg-gradient-to-br ${item.gradient} flex items-center justify-center text-2xl shadow-lg`}
                >
                  {item.icon}
                </div>
                <span className="text-xs font-semibold text-[#6c63ff] bg-[#6c63ff]/10 px-3 py-1 rounded-full">
                  {item.subtitle}
                </span>
              </div>

              {/* Title */}
              <h2 className="text-xl font-bold text-white mb-2 group-hover:text-[#6c63ff] transition-colors">
                {item.title}
              </h2>

              {/* Description */}
              <p className="text-[#a0a0b5] text-sm mb-4 flex-1 leading-relaxed">
                {item.description}
              </p>

              {/* Tags */}
              <div className="flex flex-wrap gap-2">
                {item.tags.map((tag) => (
                  <span
                    key={tag}
                    className="text-xs px-2 py-1 rounded-md bg-white/5 text-[#a0a0b5] border border-white/5"
                  >
                    {tag}
                  </span>
                ))}
              </div>

              {/* Arrow */}
              <div className="mt-4 flex items-center gap-1 text-sm text-[#6c63ff] opacity-0 group-hover:opacity-100 transition-opacity">
                Sayfaya git
                <svg
                  className="w-4 h-4 group-hover:translate-x-1 transition-transform"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    strokeWidth={2}
                    d="M9 5l7 7-7 7"
                  />
                </svg>
              </div>
            </div>
          </Link>
        ))}
      </div>

      {/* Tech Stack */}
      <div className="mt-16 text-center">
        <p className="text-[#a0a0b5] text-sm">
          Next.js • HeroUI v3 • Django • MongoDB • YOLO26 • OpenCV
        </p>
      </div>
    </div >
  );
}
