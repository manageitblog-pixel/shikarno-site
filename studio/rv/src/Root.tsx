import React from "react";
import { Composition, Still } from "remotion";
import { Short } from "./Short";
import { Episode, AvatarStill, BannerStill, WatermarkStill } from "./Episode";
import data from "./data.json";
import ep from "./ep.json";
import { GenericEpisode, EpData } from "./Generic";
import { DigestVideo, DData, DigestThumb, ShortThumb } from "./Digest";
import { Thumb2, LongThumb2 } from "./Thumb2";
import { Thumb3 } from "./Thumb3";
import { Thumb4 } from "./Thumb4";
import { Cine } from "./Cine";
import { Chat, ChatData } from "./Chat";

export const Root: React.FC = () => (
  <>
    <Composition id="Short" component={Short} durationInFrames={data.total} fps={30} width={1080} height={1920} />
    <Composition id="Episode" component={Episode} durationInFrames={ep.total} fps={30} width={1080} height={1920} />
    <Composition id="Ep" component={GenericEpisode as any} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ total: 300, scenes: [], words: [], mouth: [] } as EpData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as EpData).total })} />
    <Composition id="Cine" component={Cine as any} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ total: 300, scenes: [], words: [], mouth: [] } as EpData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as EpData).total })} />
    <Composition id="Chat" component={Chat as any} durationInFrames={300} fps={30} width={1080} height={1920}
      defaultProps={{ total: 300, question: "", model: "Gemini", prompt: "", promptFrom: 0, promptTo: 60, turns: [], reveal: 150, answer: "", reactions: [], outroFrom: 270, mouth: [] } as ChatData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as ChatData).total })} />
    <Composition id="Digest" component={DigestVideo as any} durationInFrames={300} fps={30} width={1920} height={1080}
      defaultProps={{ total: 300, num: 1, dates: "", segs: [], words: [], mouth: [], titles: [] } as DData}
      calculateMetadata={({ props }) => ({ durationInFrames: (props as DData).total })} />
    <Still id="DigestThumb" component={DigestThumb as any} width={1920} height={1080}
      defaultProps={{ num: 1, dates: "16–22 жовтня", icons: ["browser", "video", "car", "warning", "shield"], headline: "ШІ зламав 100 компаній і вимкнув нагляд" }} />
    <Still id="ShortThumb" component={ShortThumb as any} width={1080} height={1920}
      defaultProps={{ tag: "ЕКСТРЕНО", red: true, headline: "Дірка в *PHP* на 9.2 з 10", icon: "warning", mood: "judge" }} />
    <Still id="Thumb2" component={Thumb2 as any} width={1080} height={1920}
      defaultProps={{ variant: "react", pal: "fire", headline: "ШІ платить *твоєю* карткою", tag: "CHATGPT WALLET", icon: "money", mood: "shock" }} />
    <Still id="LongThumb2" component={LongThumb2 as any} width={1920} height={1080}
      defaultProps={{ variant: "react", pal: "fire", headline: "Що ШІ *знає* про тебе", kicker: "ПРИВАТНІСТЬ" }} />
    <Still id="Thumb3" component={Thumb3 as any} width={1080} height={1920}
      defaultProps={{ object: "card", text: "Він *платить*?", mood: "shock" }} />
    <Still id="Thumb3Wide" component={Thumb3 as any} width={1920} height={1080}
      defaultProps={{ object: "toggle", text: "Вимкни *це*", label: "Improve the model for everyone", wide: true }} />
    <Still id="Thumb4" component={Thumb4 as any} width={1080} height={1920}
      defaultProps={{ series: "НОВИНИ ШІ", text: "ШІ платить *твоєю* карткою", logos: ["openai"] }} />
    <Still id="Thumb4Wide" component={Thumb4 as any} width={1920} height={1080}
      defaultProps={{ series: "НОВИНИ ШІ", text: "Що *вимикають*", logos: ["openai", "googlegemini"], wide: true }} />
    <Still id="Avatar" component={AvatarStill} width={800} height={800} />
    <Still id="Banner" component={BannerStill} width={2560} height={1440} />
    <Still id="Watermark" component={WatermarkStill} width={150} height={150} />
  </>
);
