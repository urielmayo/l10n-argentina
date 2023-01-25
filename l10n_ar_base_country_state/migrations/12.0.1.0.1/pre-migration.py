# -*- coding: utf-8 -*-
import logging

_logger = logging.getLogger(__name__)


def convert_references(cr):
    try:
        _logger.info('Delete all ir.model.data referencing res.country.state of argentina')
        cr.execute("delete from ir_model_data where module='base' and name ~* 'state_ar.*';")
        _logger.info('Updating all ir.model.data referencing res.country.state of argentina to use the base states')
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_t' WHERE module='l10n_ar_base_country_state' AND name='state_tucuman';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_c' WHERE module='l10n_ar_base_country_state' AND name='state_capital_federal';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_b' WHERE module='l10n_ar_base_country_state' AND name='state_buenos_aires';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_k' WHERE module='l10n_ar_base_country_state' AND name='state_catamarca';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_x' WHERE module='l10n_ar_base_country_state' AND name='state_cordoba';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_w' WHERE module='l10n_ar_base_country_state' AND name='state_corrientes';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_h' WHERE module='l10n_ar_base_country_state' AND name='state_chaco';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_u' WHERE module='l10n_ar_base_country_state' AND name='state_chubut';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_e' WHERE module='l10n_ar_base_country_state' AND name='state_entre_rios';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_p' WHERE module='l10n_ar_base_country_state' AND name='state_formosa';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_y' WHERE module='l10n_ar_base_country_state' AND name='state_jujuy';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_l' WHERE module='l10n_ar_base_country_state' AND name='state_la_pampa';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_f' WHERE module='l10n_ar_base_country_state' AND name='state_la_rioja';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_m' WHERE module='l10n_ar_base_country_state' AND name='state_mendoza';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_n' WHERE module='l10n_ar_base_country_state' AND name='state_misiones';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_q' WHERE module='l10n_ar_base_country_state' AND name='state_neuquen';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_r' WHERE module='l10n_ar_base_country_state' AND name='state_rio_negro';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_a' WHERE module='l10n_ar_base_country_state' AND name='state_salta';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_j' WHERE module='l10n_ar_base_country_state' AND name='state_san_juan';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_d' WHERE module='l10n_ar_base_country_state' AND name='state_san_luis';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_z' WHERE module='l10n_ar_base_country_state' AND name='state_santa_cruz';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_s' WHERE module='l10n_ar_base_country_state' AND name='state_santa_fe';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_g' WHERE module='l10n_ar_base_country_state' AND name='state_sgo_del_estero';")
        cr.execute("UPDATE ir_model_data SET module='base',name='state_ar_v' WHERE module='l10n_ar_base_country_state' AND name='state_tierra_del_fuego';")
    except Exception:
        _logger.exception('Unable to process migration, manual intervention is required :/')
        cr.rollback()
    else:
        _logger.info('Sucess in application of migration :)')
        cr.commit()


def migrate(cr, version):
    _logger.warning('Before this version, the l10n was using their own states. Duplicating the base ones.')
    _logger.warning('After this version, the l10n will be using the base states.')
    cr.execute("select * from ir_model_data where name ~* '.*state_ar.*'")
    if cr.rowcount > 24:
        convert_references(cr)
    else:
        _logger.warning('Aparently the migration is not needed')
