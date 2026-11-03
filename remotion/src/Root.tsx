import React from 'react';
import {Composition} from 'remotion';
import events from './generated/events.json';
import {Lecture,Thumbnail} from './Lecture';
export const Root:React.FC=()=> <>
 <Composition id="QuantumFormalism" component={Lecture} width={events.width} height={events.height} fps={events.fps} durationInFrames={events.duration_frames} defaultProps={{showCaptions:false}}/>
 <Composition id="FormalismThumbnail" component={Thumbnail} width={1280} height={720} fps={30} durationInFrames={1}/>
</>;
