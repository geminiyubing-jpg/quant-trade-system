/**
 * Type declarations for react-simple-maps
 */
declare module 'react-simple-maps' {
  import { ComponentType, ReactNode } from 'react';

  export interface GeographyProps {
    key?: string;
    geography: Geography;
    fill?: string;
    stroke?: string;
    strokeWidth?: number;
    style?: {
      default?: object;
      hover?: object;
      pressed?: object;
    };
    onMouseEnter?: (event: React.MouseEvent, geography: Geography) => void;
    onMouseLeave?: (event: React.MouseEvent, geography: Geography) => void;
    onClick?: (event: React.MouseEvent, geography: Geography) => void;
  }

  export interface Geography {
    rsmKey: string;
    properties: {
      name: string;
      name_long?: string;
      iso_a2?: string;
      iso_a3?: string;
      continent?: string;
      [key: string]: unknown;
    };
    geometry: {
      type: string;
      coordinates: unknown;
    };
    [key: string]: unknown;
  }

  export interface MarkerProps {
    key?: string;
    coordinates: [number, number];
    children?: ReactNode;
    onClick?: (event: React.MouseEvent) => void;
    onMouseEnter?: (event: React.MouseEvent) => void;
    onMouseLeave?: (event: React.MouseEvent) => void;
  }

  export interface GeographiesProps {
    geography: string | object;
    children: (props: { geographies: Geography[] }) => ReactNode;
  }

  export interface ZoomableGroupProps {
    center?: [number, number];
    zoom?: number;
    minZoom?: number;
    maxZoom?: number;
    translateExtent?: [[number, number], [number, number]];
    onMoveStart?: (props: { coordinates: [number, number]; zoom: number }) => void;
    onMoveEnd?: (props: { coordinates: [number, number]; zoom: number }) => void;
    children?: ReactNode;
  }

  export interface ComposableMapProps {
    projection?: string;
    projectionConfig?: {
      scale?: number;
      center?: [number, number];
      rotate?: [number, number, number];
      parallels?: [number, number];
    };
    width?: number;
    height?: number;
    style?: object;
    children?: ReactNode;
  }

  export const ComposableMap: ComponentType<ComposableMapProps>;
  export const Geographies: ComponentType<GeographiesProps>;
  export const Geography: ComponentType<GeographyProps>;
  export const Marker: ComponentType<MarkerProps>;
  export const ZoomableGroup: ComponentType<ZoomableGroupProps>;
}
