import { HomeClient } from "@/components/home/home-client";

export default function Home() {
  // Pass empty projects for now since we need authentication context
  // In future iterations, we can implement proper server-side auth
  return <HomeClient serverProjects={[]} />;
}