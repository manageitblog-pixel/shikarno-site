import React from "react";
import { Composition, Still } from "remotion";
import { Short } from "./Short";
import { Episode, AvatarStill, BannerStill, WatermarkStill } from "./Episode";
import data from "./data.json";
import ep from "./ep.json";
import { GenericEpisode, EpData } from "./Generic";
import { DigestVideo, DData, DigestThumb, ShortThumb } from "./Digest";

export const Root: React.FC = () => (
  <>
    <Composition id="Short" component={Short} durationInFrames={data.total} fps={30} width={1080} height={1920} />
    <Composition id="Episode" component={Episode} durationInFrames={ep.total} fps={30} width={1080} height={1920} />
    <Composition id="Ep" component={GenericEpisode as any} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ total: 300, scenes: [], words: [], mouth: [] } as EpData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as EpData).total })} />
    <Composition id="Digest" component={DigestVideo as any} durationInFrames={300} fps={30} width={1920} height={1080}
      defaultProps={{ total: 300, num: 1, dates: "", segs: [], words: [], mouth: [], titles: [] } as DData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as DData).total })} />
    <Still id="DigestThumb" component={DigestThumb as any} width={1920} height={1080}
      defaultProps={{ num: 1, dates: "16–22 жовтня", icons: ["browser", "video", "car", "warning", "shield"], headline: "ШІ зламав 100 компаній і вимкнув нагляд" }} />
    <Still id="ShortThumb" component={ShortThumb as any} width={1080} height={1920}
      defaultProps={{ tag: "ЕКСТРЕНО", red: true, headline: "Дірка в *PHP* на 9.2 з 10", icon: "warning", mood: "judge" }} />
    <Still id="Avatar" component={AvatarStill} width={800} height={800} />
    <Still id="Banner" component={BannerStill} width={2560} height={1440} />
    <Still id="Watermark" component={WatermarkStill} width={150} height={150} />
  </>
);
