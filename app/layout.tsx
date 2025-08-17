export const metadata = {
  title: "ICEBERG",
  description: "ICEBERG demo",
};

export default function RootLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <html lang="en">
      <body style={{ fontFamily: "system-ui, Arial, sans-serif" }}>{children}</body>
    </html>
  );
}
