# -*- coding: utf-8 -*-
#
#
# (c)  Baycrest Centre for Geriatric Care ("Baycrest"), 2012, all rights reserved.
#
# No redistribution, clinical use or commercial re-sale is permitted.
# Usage-license is only granted for personal or academic usage.
# You may change sources for your private or academic use.
# If you want to contribute to the project, you need to sign a contributor's license. 
# Please contact info@thevirtualbrain.org for further details.
# Neither the name of Baycrest nor the names of any TVB contributors may be used to endorse or 
# promote products or services derived from this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY BAYCREST ''AS IS'' AND ANY EXPRESSED OR IMPLIED WARRANTIES, INCLUDING, 
# BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE 
# ARE DISCLAIMED. IN NO EVENT SHALL BAYCREST BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, 
# EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS 
# OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY 
# THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) 
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE
#
#

"""
Generate Dictionary required by the Framework to generate UI from it.
Returned dictionary will be generated from  traited definition of attributes.


.. moduleauthor:: Lia Domide <lia.domide@codemart.ro>
.. moduleauthor:: Stuart Knock <stuart.knock@gmail.com>
.. moduleauthor:: marmaduke <duke@eml.cc>

"""

import numpy
import json
from tvb.basic.logger.builder import get_logger 
from tvb.basic.traits.util import get, str_class_name
from tvb.basic.traits.core import KWARG_AVOID_SUBCLASSES, TYPE_REGISTER, KWARG_FILTERS_UI

LOG = get_logger(__name__)

INTERFACE_ATTRIBUTES_ONLY = "attributes-only"
INTERFACE_ATTRIBUTES = "attributes"



class TraitedInterfaceGenerator(object):
    """
    Bases class for interface reading and dumping. As a data descriptor, when 
    it is an attribute of the class it will compute a dictionary and return it.
    """


    def __get__(self, inst, ownr):
        
        obj = inst if inst else ownr
        if not obj.trait.bound:
            return {}
        
        label = get(obj.trait.inits.kwd, 'label', obj.trait.name)
        if not label:
            label = obj.trait.name
        intr = {'default': (obj.value or obj.trait.value) if hasattr(obj, 'value') else obj.trait.value, 
                'description': get(obj.trait.inits.kwd, 'doc'), 
                'label': self.label(label),
                'name': obj.trait.name,
                'locked': obj.trait.inits.kwd.get('locked', False),
                'required': obj.trait.inits.kwd.get('required', True)}
        
        range_value = obj.trait.inits.kwd.get('range', False)
        if range_value:
            intr['minValue'] = range_value.lo
            intr['maxValue'] = range_value.hi
            intr['stepValue'] = range_value.step
            
        if KWARG_FILTERS_UI in obj.trait.inits.kwd:
            intr[KWARG_FILTERS_UI] = json.dumps([ui_filter.to_dict() for ui_filter in 
                                                 obj.trait.inits.kwd[KWARG_FILTERS_UI]])
            
        if hasattr(obj, 'dtype'):
            intr['elementType'] = getattr(obj, 'dtype')
            
        if get(obj.trait, 'wraps', False):
            if isinstance(obj.trait.wraps, tuple):
                intr['type'] = str(obj.trait.wraps[0].__name__)  
            else:
                intr['type'] = str(obj.trait.wraps.__name__)
                
            if intr['type'] == 'dict' and isinstance(intr['default'], dict):
                intr['attributes'], intr['elementType'] = self.__prepare_dictionary(intr['default'])
                if len(intr['attributes']) < 1:
                    ## Dictionary without any sub-parameter
                    return {}
                
        ##### ARRAY specific processing ########################################
        if ('Array' in [str(i.__name__) for i in ownr.mro()]):
            intr['type'] = 'array'
            intr['elementType'] = str(inst.dtype)
            intr['quantifier'] = 'manual'
            if (obj.trait.value is not None and isinstance(obj.trait.value, numpy.ndarray)):
                # Make sure arrays are displayed in a compatible form: [1, 2, 3]
                intr['default'] = str(obj.trait.value.tolist())
         
        ##### TYPE & subclasses specifics ######################################
        elif ('Type' in [str(i.__name__) for i in ownr.mro()] 
              and (obj.__module__ != 'tvb.basic.traits.types_basic' 
                   or 'Range' in [str(i.__name__) for i in ownr.mro()])
                        or 'Enumerate' in [str(i.__name__) for i in ownr.mro()]):
            
            # Populate Attributes for current entity
            attrs = sorted(getattr(obj, 'trait').values(), key=lambda entity: entity.trait.order_number)
            attrs = [val.interface for val in attrs if val.trait.order_number >= 0]
            attrs = [attr for attr in attrs if attr is not None and len(attr)>0]
            intr['attributes'] = attrs
            
            if obj.trait.bound == INTERFACE_ATTRIBUTES_ONLY:
                # We need to do this, to avoid infinite loop on attributes 
                # of class Type with no subclasses
                return intr

            if (obj.trait.select_multiple):
                intr['type'] = 'selectMultiple'
            else:
                intr['type'] = 'select'
        
        ##### MAPPED_TYPE specifics ############################################
            if 'MappedType' in [str(i.__name__) for i in ownr.mro()]:
                intr['datatype'] = True
                #### For simple DataTypes, cut options and attributes
                intr['options'] = []
                if not ownr._ui_complex_datatype:
                    intr['attributes'] = []
                    ownr_class = ownr.__class__
                else:
                    ownr_class = ownr._ui_complex_datatype
                if 'MetaType' in ownr_class.__name__:
                    ownr_class = ownr().__class__
                intr['type'] = ownr_class.__module__ + '.' + ownr_class.__name__
                
            else:
        ##### TYPE (not MAPPED_TYPE) again ####################################
                intr['attributes'] = []
                # Build options list
                intr['options'] = []
                if 'Enumerate' in obj.__class__.__name__:
                    for val in obj.trait.options:
                        intr['options'].append({'name': val,
                                                'value': val})
                    intr['default'] = obj.trait.value
                    return intr
                else:
                    for opt in TYPE_REGISTER.subclasses(ownr, KWARG_AVOID_SUBCLASSES in obj.trait.inits.kwd):
                        if hasattr(obj, 'value') and obj.value is not None and isinstance(obj.value, opt):
                            ## fill option currently selected with attributes from instance
                            opt = obj.value
                            opt_class = opt.__class__
                        else:
                            opt_class = opt
                        opt.trait.bound = INTERFACE_ATTRIBUTES_ONLY
                        intr['options'].append({'name': get(opt, '_ui_name', opt_class.__name__),
                                                'value': str_class_name(opt_class, short_form=True),
                                                'class': str_class_name(opt_class, short_form=False),
                                                'description': opt_class.__doc__,
                                                'attributes': opt.interface['attributes'] })
                    
            if (intr['default'] is not None and intr['default'].__class__):
                intr['default'] = str(intr['default'].__class__.__name__)
                if intr['default'] == 'RandomState':
                    intr['default'] = 'RandomStream'
            else:
                intr['default'] = None
        
        return intr


    def __prepare_dictionary(self, dictionary):
        """
        From base.Dict -> default [isinstance(dict)], prepare an interface specific tree.
        """
        result = []
        element_type = None
        for key in dictionary:
            entry = {}
            value = dictionary[key]
            entry['label'] = key
            entry['name'] = key
            if type(value).__name__ == 'dict':
                entry['attributes'], entry['elementType'] = self.__prepare_dictionary(value)
                value = ''
            entry['default'] = str(value)
            
            if hasattr(value, 'tolist') or 'Array' in [str(i.__name__) for i in type(value).mro()]:
                entry['type'] = 'array'
                if not hasattr(value, 'tolist'):
                    entry['default'] = str(value.trait.value)
            else:
                entry['type'] = type(value).__name__
                
            element_type = entry['type']
            result.append(entry)
        return result, element_type


    def __set__(self, inst, val):
        """
        Given a hierarchical dictionary of the kind generated by __get__, with the 
        chosen options, we should be able to fully instantiate a class.
        """
        raise NotImplementedError

    
    @staticmethod
    def label(text):
        """
        Create suitable UI label given text.
        Enforce starts with upper-case.
        """
        return  text[0].upper() + text[1:]
    
