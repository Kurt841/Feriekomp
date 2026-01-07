'use client';

import React from 'react';
import { useForm } from 'react-hook-form';
import { zodResolver } from '@hookform/resolvers/zod';
import { FaUmbrellaBeach } from 'react-icons/fa';
import { beregnSchema, type BeregnInput, type BeregnOutput } from '@/lib/validation';
import { useRegistrerBesok, useBeregnKompensasjon, useForklarBeregning } from '@/lib/api';

const NOK = new Intl.NumberFormat('nb-NO', {
  style: 'currency',
  currency: 'NOK',
  maximumFractionDigits: 0
});

const UserInterface = () => {
  useRegistrerBesok();

  const {
    register,
    handleSubmit,
    watch,
    formState: { errors, isSubmitting },
  } = useForm({
    resolver: zodResolver(beregnSchema),
    defaultValues: {
      startdato_ferie: '',
      sluttdato_ferie: '',
      dato_legebesok: '',
      total_reisebelop: 0,
      antall_personer: 1,
      antall_dager_sengeleie: 0,
      ekstra_dag_for_legebesok: false,
    },
  });

  const startdato = watch('startdato_ferie');
  const sluttdato = watch('sluttdato_ferie');

  const beregnMutation = useBeregnKompensasjon();
  const forklarMutation = useForklarBeregning();

  const lagLokalForklaring = (input: BeregnInput, resultat: BeregnOutput) => {
    const linjer: string[] = [];
    linjer.push(
      `Beregningen tar utgangspunkt i en reise på ${resultat.total_feriedager} dager og dokumentert sykdom i ${resultat.gyldige_dager} dager.`
    );
    linjer.push(
      `Dagsprisen per person er ${NOK.format(resultat.dagspris_per_person)} (maks 2 000 kr).`
    );
    linjer.push(
      `${resultat.dekkede_personer} person(er) dekkes. Eventuell ekstra dag for legebesøk: ${input.ekstra_dag_for_legebesok ? 'ja' : 'nei'}.`
    );
    linjer.push(
      `Totalt: ${resultat.gyldige_dager} × ${NOK.format(resultat.dagspris_per_person)} × ${resultat.dekkede_personer} = ${NOK.format(resultat.total_kompensasjon)}.`
    );
    return linjer.join('\n');
  };

  const onSubmit = async (data: BeregnInput) => {
    try {
      const resultat = await beregnMutation.mutateAsync(data);

      const enableForklaring = process.env.NEXT_PUBLIC_ENABLE_AI_EXPLANATION === 'true';
      if (enableForklaring) {
        try {
          await forklarMutation.mutateAsync({ input: data, resultat });
        } catch {
          if (process.env.NODE_ENV === 'development') {
            console.warn('AI forklaring feilet, bruker lokal forklaring');
          }
        }
      }
    } catch (error) {
      if (process.env.NODE_ENV === 'development') {
        console.error('Beregning feilet:', error);
      }
    }
  };

  const resultat = beregnMutation.data;
  const forklaring = forklarMutation.data;

  return (
    <div className="w-full min-h-screen flex flex-col items-center justify-center py-12 px-4 bg-transparent">
      <div className="w-full max-w-7xl rounded-2xl shadow-xl p-0 flex flex-col md:flex-row gap-10 border border-gray-800 bg-gray-900">
        <div className="flex-1 flex flex-col gap-8 p-4 md:p-8">
          {/* Header */}
          <div className="flex flex-col items-center gap-2 mb-2">
            <FaUmbrellaBeach size="2.5rem" color="#fafafa" />
            <h1 className="text-2xl font-extrabold text-gray-100 tracking-tight">
              Feriekompensasjon Kalkulator
            </h1>
          </div>

          <div className="flex flex-col gap-8 w-full md:flex-row items-stretch">
            {/* Huskeliste */}
            <div className="flex-1 flex flex-col gap-2 bg-gray-800 rounded-xl p-4 border border-gray-700 shadow-sm h-full">
              <h2 className="text-base font-bold mb-1 text-gray-200 flex items-center gap-2">
                Huskeliste
              </h2>
              <ul className="list-disc pl-4 text-gray-200 text-base space-y-7">
                <li>Maks 2.000 kr per dag per person</li>
                <li>Maks 2 personer kan dekkes</li>
                <li>Maks 10 dager kan kompenseres</li>
                <li>Kompensasjon gis kun ved akutt sykdom/skade dokumentert av lege</li>
                <li>Gjelder kun for reiser inntil 5 uker</li>
              </ul>
            </div>

            {/* Form */}
            <form
              onSubmit={handleSubmit(onSubmit)}
              className="flex-1 flex flex-col gap-4 bg-gray-800 rounded-xl p-4 md:p-8 border border-gray-700 shadow-sm h-full"
            >
              {/* Startdato */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Startdato for ferien</span>
                <input
                  type="date"
                  {...register('startdato_ferie')}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                />
                {errors.startdato_ferie && (
                  <span className="text-red-400 text-sm">{errors.startdato_ferie.message}</span>
                )}
              </label>

              {/* Sluttdato */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Sluttdato for ferien</span>
                <input
                  type="date"
                  {...register('sluttdato_ferie')}
                  min={startdato || undefined}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                />
                {errors.sluttdato_ferie && (
                  <span className="text-red-400 text-sm">{errors.sluttdato_ferie.message}</span>
                )}
              </label>

              {/* Total reisebeløp */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Total reisebeløp</span>
                <input
                  type="number"
                  {...register('total_reisebelop')}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                  placeholder="f.eks. 10000"
                />
                {errors.total_reisebelop && (
                  <span className="text-red-400 text-sm">{errors.total_reisebelop.message}</span>
                )}
              </label>

              {/* Antall personer */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Antall personer (1-10)</span>
                <input
                  type="number"
                  {...register('antall_personer')}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                  placeholder="1-10"
                />
                {errors.antall_personer && (
                  <span className="text-red-400 text-sm">{errors.antall_personer.message}</span>
                )}
              </label>

              {/* Dato for legebesøk */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Dato for legebesøk</span>
                <input
                  type="date"
                  {...register('dato_legebesok')}
                  min={startdato || undefined}
                  max={sluttdato || undefined}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                />
                {errors.dato_legebesok && (
                  <span className="text-red-400 text-sm">{errors.dato_legebesok.message}</span>
                )}
              </label>

              {/* Antall dager sengeleie */}
              <label className="flex flex-col gap-1 text-gray-200 text-base">
                <span className="font-medium">Antall dager sengeleie</span>
                <input
                  type="number"
                  {...register('antall_dager_sengeleie')}
                  className="border border-gray-700 bg-gray-900 rounded-lg p-2 text-base focus:ring-2 focus:ring-gray-500 transition w-full text-gray-100"
                  placeholder="f.eks. 3"
                />
                {errors.antall_dager_sengeleie && (
                  <span className="text-red-400 text-sm">
                    {errors.antall_dager_sengeleie.message}
                  </span>
                )}
              </label>

              {/* Ekstra dag for legebesøk */}
              <label className="flex items-center gap-2 text-gray-200 text-base">
                <input
                  type="checkbox"
                  {...register('ekstra_dag_for_legebesok')}
                  className="accent-gray-400 w-4 h-4"
                />
                <span>Ekstra dag for legebesøk</span>
              </label>

              {/* Submit button */}
              <button
                type="submit"
                className="bg-gray-700 text-gray-100 px-6 py-3 rounded-lg text-lg md:text-xl hover:bg-gray-600 transition font-bold mt-1 w-full shadow-md hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-gray-500 disabled:opacity-50 disabled:cursor-not-allowed"
                disabled={isSubmitting || beregnMutation.isPending}
              >
                {isSubmitting || beregnMutation.isPending ? 'Beregner...' : 'Beregn kompensasjon'}
              </button>

              {/* Error message */}
              {beregnMutation.isError && (
                <div
                  role="alert"
                  aria-live="polite"
                  className="w-full bg-gray-700 border border-red-700 text-red-400 px-4 py-2 rounded mb-3 text-center text-base font-semibold"
                >
                  {beregnMutation.error instanceof Error
                    ? beregnMutation.error.message
                    : 'Noe gikk galt. Prøv igjen.'}
                </div>
              )}
            </form>
          </div>

          {/* Resultat + Forklaring */}
          {resultat && (
            <div className="w-full flex flex-col md:flex-row gap-6">
              {/* Resultat-kort */}
              <div className="flex-1">
                <div className="flex flex-col gap-2 bg-gray-800 rounded-xl p-4 border border-gray-700 shadow-sm relative">
                  <button
                    className="absolute top-2 right-2 text-gray-400 hover:text-red-400 text-2xl font-bold focus:outline-none"
                    aria-label="Lukk resultat"
                    onClick={() => beregnMutation.reset()}
                    type="button"
                  >
                    &times;
                  </button>
                  <h2 className="text-base font-bold mb-1 text-gray-200 flex items-center gap-2">
                    Resultat
                  </h2>
                  <div className="space-y-2 text-base">
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-200">Dagspris per person:</span>
                      <span className="text-gray-100 whitespace-nowrap">
                        {NOK.format(resultat.dagspris_per_person)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-200">Dekkede personer:</span>
                      <span className="text-gray-100 whitespace-nowrap">
                        {resultat.dekkede_personer}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-200">Gyldige dager:</span>
                      <span className="text-gray-100 whitespace-nowrap">
                        {resultat.gyldige_dager}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-200">Total kompensasjon:</span>
                      <span className="text-gray-100 whitespace-nowrap">
                        {NOK.format(resultat.total_kompensasjon)}
                      </span>
                    </div>
                    <div className="flex justify-between">
                      <span className="font-medium text-gray-200">Antall reisedager:</span>
                      <span className="text-gray-100 whitespace-nowrap">
                        {resultat.total_feriedager}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              {/* Forklarings-kort */}
              <div className="flex-1">
                <div className="flex flex-col gap-2 bg-gray-800 rounded-xl p-4 border border-gray-700 shadow-sm">
                  <h2 className="text-base font-bold mb-1 text-gray-200 flex items-center gap-2">
                    <span role="img" aria-label="robot">
                      🤖
                    </span>{' '}
                    Forklaring
                  </h2>
                  <div className="text-base text-gray-100 whitespace-pre-wrap">
                    {forklarMutation.isPending ? (
                      <span className="text-gray-400">Genererer forklaring...</span>
                    ) : forklarMutation.isError ? (
                      <span className="text-gray-400">
                        {lagLokalForklaring(watch() as BeregnInput, resultat)}
                      </span>
                    ) : forklaring ? (
                      forklaring.forklaring
                    ) : (
                      lagLokalForklaring(watch() as BeregnInput, resultat)
                    )}
                  </div>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default UserInterface;
