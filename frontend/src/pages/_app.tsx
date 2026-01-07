import "@/styles/globals.css";
import type { AppProps } from "next/app";
import Header from "@/components/Header";
import Footer from "@/components/Footer";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export default function App({ Component, pageProps }: AppProps) {
  const [queryClient] = useState(() => new QueryClient({
    defaultOptions: {
      queries: {
        staleTime: 60 * 1000,
        retry: 1,
        refetchOnWindowFocus: false,
      },
    },
  }));

  return (
    <QueryClientProvider client={queryClient}>
      <Header />
      <Component {...pageProps} />
      <Footer />
    </QueryClientProvider>
  );
}
