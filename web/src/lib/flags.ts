// Ported from styles.py TEAM_FLAGS
export const TEAM_FLAGS: Record<string, string> = {
  Germany: "🇩🇪", Paraguay: "🇵🇾", France: "🇫🇷", Sweden: "🇸🇪",
  "South Africa": "🇿🇦", Canada: "🇨🇦", Netherlands: "🇳🇱", Morocco: "🇲🇦",
  Portugal: "🇵🇹", Croatia: "🇭🇷", Spain: "🇪🇸", Austria: "🇦🇹",
  "United States": "🇺🇸", "Bosnia and Herzegovina": "🇧🇦", Belgium: "🇧🇪",
  Senegal: "🇸🇳", Brazil: "🇧🇷", Japan: "🇯🇵", "Ivory Coast": "🇨🇮",
  Norway: "🇳🇴", Mexico: "🇲🇽", Ecuador: "🇪🇨", England: "🏴󠁧󠁢󠁥󠁮󠁧󠁿",
  "DR Congo": "🇨🇩", Argentina: "🇦🇷", "Cape Verde": "🇨🇻", Australia: "🇦🇺",
  Egypt: "🇪🇬", Switzerland: "🇨🇭", Algeria: "🇩🇿", Colombia: "🇨🇴",
  Ghana: "🇬🇭",
};

export function flag(team: string): string {
  return TEAM_FLAGS[team] ?? "🏳️";
}
