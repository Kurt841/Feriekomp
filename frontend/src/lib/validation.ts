import { z } from 'zod';

/**
 * Zod-skjema for feriekompensasjon beregning
 * Matcher Pydantic-skjemaet i backend
 */
export const beregnSchema = z.object({
  startdato_ferie: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Dato må være i YYYY-MM-DD format'),
  sluttdato_ferie: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Dato må være i YYYY-MM-DD format'),
  dato_legebesok: z.string().regex(/^\d{4}-\d{2}-\d{2}$/, 'Dato må være i YYYY-MM-DD format'),
  total_reisebelop: z.coerce.number()
    .min(0, 'Reisebeløp kan ikke være negativt')
    .max(1_000_000, 'Reisebeløp kan ikke overstige 1 000 000 kr'),
  antall_personer: z.coerce.number()
    .int('Antall personer må være et heltall')
    .min(1, 'Må ha minst 1 person')
    .max(10, 'Maksimalt 10 personer'),
  antall_dager_sengeleie: z.coerce.number()
    .int('Antall dager må være et heltall')
    .min(0, 'Kan ikke være negativt')
    .max(35, 'Maksimalt 35 dager'),
  ekstra_dag_for_legebesok: z.boolean(),
})
.refine((data) => {
  const start = new Date(data.startdato_ferie);
  const slutt = new Date(data.sluttdato_ferie);
  return slutt > start;
}, {
  message: 'Sluttdato må være etter startdato',
  path: ['sluttdato_ferie'],
})
.refine((data) => {
  const start = new Date(data.startdato_ferie);
  const slutt = new Date(data.sluttdato_ferie);
  const lege = new Date(data.dato_legebesok);
  return lege >= start && lege <= slutt;
}, {
  message: 'Dato for legebesøk må være innenfor ferieperioden',
  path: ['dato_legebesok'],
})
.refine((data) => {
  const start = new Date(data.startdato_ferie);
  const slutt = new Date(data.sluttdato_ferie);
  const totalDager = Math.floor((slutt.getTime() - start.getTime()) / (1000 * 60 * 60 * 24)) + 1;
  return totalDager <= 35;
}, {
  message: 'Ferie kan ikke overstige 35 dager (5 uker)',
  path: ['sluttdato_ferie'],
});

export type BeregnInput = z.infer<typeof beregnSchema>;

export interface BeregnOutput {
  gyldige_dager: number;
  dagspris_per_person: number;
  dekkede_personer: number;
  total_kompensasjon: number;
  total_feriedager: number;
  maks_dagspris?: number;
  forklaring?: string;
}

export interface BesokOutput {
  antall: number;
  sist_oppdatert: string;
}
