import Image from "next/image";
import Link from "next/link";

export default function HomePage() {
  return (
    <div className="flex flex-col items-center justify-center min-h-screen p-4 text-center">
      <h1 className="text-4xl font-bold mb-6">ようこそ</h1>
      <div className="space-x-4">
        <Link href="/sign-in" 
              className="px-4 py-2 bg-primary text-primary-foreground rounded-md hover:bg-primary/90 transition-colors">
          ログイン
        </Link>
        <Link href="/dashboard" 
              className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md hover:bg-secondary/90 transition-colors">
          ダッシュボード
        </Link>
      </div>
    </div>
  );
}
